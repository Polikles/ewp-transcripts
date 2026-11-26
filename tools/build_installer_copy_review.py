"""Build an editable installer copy inventory without changing product or license text.

Run in a disposable environment with openpyxl==3.1.5. See docs/installer-copy-review/README.md.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import html
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = [
    "ID",
    "Obszar",
    "Kontekst",
    "EN",
    "PL",
    "Decyzja",
    "Uwagi do korekty",
    "Parametry / kod",
    "Źródła",
    "EN oryginał",
    "PL oryginał",
]
SHEETS = [
    "Interfejs",
    "Pelne_komunikaty",
    "Raport_i_terminal",
    "Notices_projektu",
    "Oryginalne_licencje",
    "Linki",
    "Dane_i_formaty",
    "Archiwum_ID",
]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def cs_literals(source):
    """Scan normal/verbatim/raw C# literals, ignoring line and block comments."""
    i = 0
    while i < len(source):
        if source.startswith("//", i):
            end = source.find("\n", i)
            i = len(source) if end < 0 else end + 1
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = len(source) if end < 0 else end + 2
            continue
        match = (
            re.match(r'(\$*@?|@\$?)("+)', source[i:])
            if source[i] in "@$"
            else re.match(r'()("+)', source[i:])
        )
        if not match:
            i += 1
            continue
        start = i
        prefix, quotes = match.groups()
        if len(quotes) >= 3:
            end = source.find(quotes, i + len(prefix) + len(quotes))
            if end < 0:
                raise ValueError("Unclosed C# raw string")
            value = source[i + len(prefix) + len(quotes) : end]
            end += len(quotes)
            kind = "raw"
        else:
            end = i + len(prefix) + 1
            chars = []
            while end < len(source):
                if source[end] == '"':
                    if "@" in prefix and source[end : end + 2] == '""':
                        chars.append('"')
                        end += 2
                        continue
                    end += 1
                    break
                if source[end] == "\\" and "@" not in prefix:
                    code = source[end + 1 : end + 2]
                    escapes = {
                        "n": "\n",
                        "r": "\r",
                        "t": "\t",
                        '"': '"',
                        "'": "'",
                        "\\": "\\",
                        "0": "\0",
                    }
                    if code in {"u", "U"}:
                        size = 8 if code == "U" else 4
                        chars.append(chr(int(source[end + 2 : end + 2 + size], 16)))
                        end += size + 2
                        continue
                    chars.append(escapes.get(code, "\\" + code))
                    end += 2
                    continue
                chars.append(source[end])
                end += 1
            value = "".join(chars)
            kind = "interpolated" if "$" in prefix else "verbatim" if "@" in prefix else "normal"
        yield {
            "start": start,
            "end": end,
            "text": value,
            "kind": kind,
            "line": source.count("\n", 0, start) + 1,
        }
        i = end


def owner_at(source, position):
    declarations = list(
        re.finditer(
            (
                "\\b(?:void|string\\??|bool|Task(?:<[^>]+>)?|Window|p"
                "ublic\\s+CredentialDialog)\\s+(\\w+)\\s*(?:\\(|=>)"
            ),
            source[:position],
        )
    )
    return declarations[-1].group(1) if declarations else "inicjalizacja / stałe"


def area(file, method):
    if file == "Credentials.cs":
        return "Okno tokenu HF / klucza OR"
    if file == "WizardKeys.cs":
        return "4. Klucz OpenRouter / instrukcja"
    if file == "WizardModels.cs":
        return "3. Modele / naprawa modeli"
    if file == "WizardRollback.cs":
        return "Przywracanie wersji"
    if file == "WizardProgress.cs":
        return "Instalacja / postęp / pobieranie"
    if method in {"CreateHfHelp", "ShowHfHelp"}:
        return "Pomoc Hugging Face"
    if method in {
        "RenderLocation",
        "LocationProblem",
        "RefreshLocation",
        "ModelSpaceProblem",
        "HostText",
        "RenderHostRows",
    }:
        return "2. Lokalizacja / test komputera / miejsce"
    if method in {"RenderWelcome", "OperationName", "OperationHelp"}:
        return "1. Działanie / opis operacji"
    if method in {"RenderProgress", "ProgressMessage", "AddLog", "SaveReport"}:
        return "Wynik / postęp / raport"
    if method == "RenderConfirmation":
        return "Potwierdzenie odinstalowania"
    return "Nawigacja / wspólne / komunikaty"


def expression_text(node):
    """Preserve complete literal alternatives and parameterize runtime values."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        pieces = []
        for value in node.values:
            pieces.append(
                value.value
                if isinstance(value, ast.Constant)
                else "{" + ast.unparse(value.value) + "}"
            )
        return ["".join(pieces)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = expression_text(node.left), expression_text(node.right)
        return [a + b for a in left for b in right]
    if isinstance(node, ast.IfExp):
        return expression_text(node.body) + expression_text(node.orelse)
    return ["{" + ast.unparse(node) + "}"]


def inventory(bundle):
    historical = list(
        csv.DictReader((ROOT / "installer/ui-en-pl.csv").open(encoding="utf-8-sig", newline=""))
    )
    old_pairs = {(row["EN"], row["PL"]): row for row in historical}
    old_en = {row["EN"]: row for row in historical}
    rows = []
    known = {}
    preserved = set()
    coverage = []
    inputs = {}
    binding_count = Counter()
    ui_pairs = []

    def add(
        sheet,
        en,
        pl=None,
        context="",
        location="",
        notes="",
        parameters="",
        decision="DO KOREKTY",
        key=None,
        group=None,
    ):
        if not en.strip():
            return None
        pl = en if pl is None else pl
        if "\0" in en or "\0" in pl:
            raise ValueError("NUL is not review copy")
        identity = (sheet, key or en, pl if key is None else "")
        if identity in known:
            row = known[identity]
            for column, value in [("Źródła", location), ("Kontekst", context)]:
                if value and value not in row[column].split("\n"):
                    row[column] += ("\n" if row[column] else "") + value
            return row
        old = old_pairs.get((en, pl)) if sheet == "Interfejs" else None
        if (
            old is None
            and sheet == "Interfejs"
            and en in old_en
            and old_en[en]["ID"] not in preserved
        ):
            old = old_en[en]
            notes += " Aktualne źródło ma inną wersję PL niż stary plik pomocniczy."
        ident = (
            old["ID"]
            if old
            else "installer."
            + {
                "Interfejs": "ui",
                "Pelne_komunikaty": "template",
                "Raport_i_terminal": "log",
                "Notices_projektu": "notice",
                "Oryginalne_licencje": "legal",
                "Linki": "link",
                "Dane_i_formaty": "data",
                "Archiwum_ID": "archive",
            }[sheet]
            + "."
            + digest(sheet + "\0" + (key or en) + "\0" + (pl if key is None else ""))[:16]
        )
        if old:
            preserved.add(ident)
        row = dict(
            zip(
                COLUMNS,
                [
                    ident,
                    group or sheet,
                    context,
                    en,
                    pl,
                    decision,
                    notes.strip(),
                    parameters,
                    location,
                    en,
                    pl,
                ],
                strict=True,
            )
        )
        row["sheet"] = sheet
        known[identity] = row
        rows.append(row)
        return row

    fixed = {
        "English": "English",
        "Polski": "Polski",
        "Hugging Face": "Hugging Face",
        "OpenRouter": "OpenRouter",
        "EwP Transcripts": "EwP Transcripts",
        "EwP Setup": "EwP Setup",
        "OK": "OK",
        "SHA OK": "SHA OK",
        "FFmpeg / ffprobe": "FFmpeg / ffprobe",
        "Settings → Access Tokens": "Settings → Access Tokens",
    }
    cs_files = sorted((ROOT / "installer/windows").glob("*.cs"))
    for file in cs_files:
        if file.name == "WizardTests.cs":
            continue
        rel = file.relative_to(ROOT).as_posix()
        source = file.read_text()
        inputs[rel] = digest(source)
        tokens = list(cs_literals(source))
        consumed = {}
        for index, token in enumerate(tokens[:-1]):
            following = tokens[index + 1]
            before = source[max(0, token["start"] - 16) : token["start"]]
            if (
                re.search(r"\bT\(\s*$", before)
                and source[token["end"] : following["start"]].strip() == ","
            ):
                method = owner_at(source, token["start"])
                en, pl = token["text"], following["text"]
                note = (
                    "Fragment; pełne złożone zdanie jest także w Pelne_komunikaty."
                    if en.endswith((": ", " · ", " ")) or en.startswith(" ")
                    else ""
                )
                if "Disk space" in en or "GB " in en:
                    note += (
                        " Do skrócenia i ujednolicenia: próg instalacji25 G"
                        "B obejmuje20 GB i5 GB marginesu."
                    )
                row = add(
                    "Interfejs",
                    en,
                    pl,
                    area(file.name, method) + " / " + method,
                    f"{rel}:{token['line']}",
                    note,
                )
                consumed[index] = consumed[index + 1] = row["ID"] if row else "empty-copy"
                ui_pairs.append((rel, token["line"], en, pl))
                binding_count["T"] += 1
        if file.name == "Credentials.cs":
            for index, token in enumerate(tokens[:-1]):
                following = tokens[index + 1]
                if (
                    index not in consumed
                    and index + 1 not in consumed
                    and source[token["end"] : following["start"]].strip() == ","
                    and re.search(r"[a-z][ .]", token["text"])
                    and re.search("[ąćęłńóśźż]", following["text"])
                ):
                    row = add(
                        "Interfejs",
                        token["text"],
                        following["text"],
                        "Okno tokenu HF / klucza OR — błąd sprawdzania",
                        f"{rel}:{token['line']}",
                    )
                    consumed[index] = consumed[index + 1] = row["ID"]
                    binding_count["CredentialResult"] += 1
        for index, token in enumerate(tokens):
            value = token["text"]
            location = f"{rel}:{token['line']}"
            classification = consumed.get(index)
            method = owner_at(source, token["start"])
            if classification is None:
                if value in fixed:
                    row = add(
                        "Interfejs",
                        value,
                        fixed[value],
                        area(file.name, method),
                        location,
                        "Stała nazwa/etykieta; obecnie jednakowa w obu językach.",
                    )
                    classification = row["ID"]
                elif file.name == "Program.cs" and " / " in value and "Cannot prepare" in value:
                    en, pl = value.split(" / ", 1)
                    row = add(
                        "Interfejs",
                        en,
                        pl,
                        "Błąd uruchomienia EXE — komunikat dwujęzyczny w jednym oknie",
                        location,
                    )
                    classification = row["ID"]
                elif value.startswith('{"stage":'):
                    data = json.loads(value)
                    if data.get("stage") != "test":
                        row = add(
                            "Raport_i_terminal",
                            data["message"],
                            context="Windows / uprawnienia / techniczny komunikat",
                            location=location,
                            notes="Aktualnie EN także w polskiej wersji; kod błędu zachować.",
                            parameters=data["message"].split(":", 1)[0],
                        )
                        classification = row["ID"]
                    else:
                        classification = "self-test-only"
                elif token["kind"] == "raw":
                    # Embedded PowerShell bootstrap is code, not a single message.
                    for match in re.finditer(r"(?:throw|Write-Host)\s+'([^']+)'", value):
                        row = add(
                            "Raport_i_terminal",
                            match.group(1),
                            context="Osadzony bootstrap PowerShell",
                            location=location,
                            notes="Aktualnie angielski komunikat techniczny.",
                        )
                    classification = "embedded-code; inner messages inventoried"
                elif (
                    re.search(r"[A-Za-z]{3} [A-Za-z]", value)
                    and file.name not in {"Credits.cs", "Branding.cs"}
                    and "Segoe UI" not in value
                    and "self-test" not in value
                ):
                    row = add(
                        "Raport_i_terminal",
                        value,
                        context=f"{file.name} / {method}",
                        location=location,
                        notes="Nielokalizowany tekst / wyjątek; obecnie EN także w PL.",
                    )
                    classification = row["ID"]
                else:
                    classification = "code/format/path/empty/notice-formatter/self-test"
            coverage.append(
                {
                    "source": location,
                    "literal_sha256": digest(value),
                    "classification": classification,
                }
            )
        for token in tokens:
            if token["text"].startswith("https://"):
                url = token["text"]
                api = "/api/" in url
                add(
                    "Linki",
                    url,
                    url,
                    area(file.name, owner_at(source, token["start"])),
                    f"{rel}:{token['line']}",
                    "Endpoint techniczny (sprawdzanie klucza), nie link instrukcji."
                    if api
                    else (
                        "Prefiks adresu instrukcji HF; kompletne linki EN i PL "
                        "są w osobnych wierszach."
                    )
                    if url.endswith("HUGGINGFACE_ACCESS")
                    else (
                        "Adres linku otwieranego w instrukcji. Tekst linku "
                        "w Interfejs / Pelne_komunikaty."
                    ),
                    decision="NIE ZMIENIAĆ" if api else "DO OCENY",
                    key=url,
                )

    for language, suffix in [("EN", ""), ("PL", "_PL")]:
        target = (
            "https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/HUGGINGFACE_ACCESS"
            + suffix
            + ".md"
        )
        add(
            "Linki",
            target,
            target,
            "Pełna instrukcja HF / " + language,
            "installer/windows/Wizard.cs:495",
            "Pełny adres po złożeniu prefiksu i sufiksu języka.",
            key=target,
        )

    # Complete composed copy, not just the editable fragments used by T().
    template_path = ROOT / "docs/installer-copy-review/templates.json"
    inputs[str(template_path.relative_to(ROOT))] = hashlib.sha256(
        template_path.read_bytes()
    ).hexdigest()
    templates = json.loads(template_path.read_text())
    for template in templates:
        parameters = ", ".join(sorted(set(re.findall(r"\{[^{}]+\}", template["en"]))))
        assert set(re.findall(r"\{[^{}]+\}", template["en"])) == set(
            re.findall(r"\{[^{}]+\}", template["pl"])
        ), template["key"]
        add(
            "Pelne_komunikaty",
            template["en"],
            template["pl"],
            template["context"],
            template["source"],
            template.get(
                "notes",
                "Pełny widoczny tekst. Zawartość nawiasów {…} zastępuje dane; zachowaj te nazwy.",
            ),
            parameters,
            key=template["key"],
        )

    python_files = [
        "installer/manager.py",
        "scripts/setup-models.py",
        "src/ewp_transcripts/credentials.py",
        "src/ewp_transcripts/doctor.py",
    ]
    for rel in python_files:
        source = (ROOT / rel).read_text()
        inputs[rel] = digest(source)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = ast.unparse(node.func)
            values = []
            if name in {
                "emit",
                "check",
                "input",
                "print",
                "getpass.getpass",
                "InstallError",
                "SystemExit",
                "ValueError",
                "CredentialStoreError",
            }:
                offset = 1 if name == "emit" else 2 if name == "check" else 0
                if len(node.args) > offset and isinstance(
                    node.args[offset], (ast.Constant, ast.JoinedStr, ast.BinOp, ast.IfExp)
                ):
                    values += expression_text(node.args[offset])
            values += [
                text
                for keyword in node.keywords
                if keyword.arg in {"message", "help"}
                for text in expression_text(keyword.value)
            ]
            for value in values:
                if value.startswith("{") and value.endswith("}") and value.count("{") == 1:
                    continue
                if len(value) < 3 or not re.search("[A-Za-z]", value):
                    continue
                row = add(
                    "Raport_i_terminal",
                    value,
                    context=f"{rel} / {name}",
                    location=f"{rel}:{node.lineno}",
                    notes=(
                        "Oryginalny komunikat EN w dzienniku/terminalu/diag"
                        "nostyce także przy PL. Polską wersję można zapropo"
                        "nować w PL."
                    ),
                    parameters=", ".join(sorted(set(re.findall(r"\{[^{}]+\}", value)))),
                )
                if row:
                    binding_count["python-message"] += 1
        # Python lifecycle creates a Linux desktop entry and launcher display names.
        if rel == "installer/manager.py":
            for token in ast.walk(tree):
                if (
                    isinstance(token, ast.Constant)
                    and isinstance(token.value, str)
                    and ("Press Ctrl+C" in token.value or token.value.startswith("[Desktop Entry]"))
                ):
                    value = token.value
                    if "[Desktop Entry]" in value:
                        for line in value.splitlines():
                            if line.startswith(("Name=", "Comment=")):
                                add(
                                    "Interfejs",
                                    line.split("=", 1)[1],
                                    context="Wpis aplikacji Ubuntu / skrót",
                                    location=f"{rel}:{token.lineno}",
                                    notes="Obecnie identyczny tekst także w PL.",
                                )
                    else:
                        add(
                            "Raport_i_terminal",
                            value,
                            context="Uruchamianie / terminal",
                            location=f"{rel}:{token.lineno}",
                            notes="Tekst uruchamiania; zachowaj skrót Ctrl+C.",
                        )

    script_files = [
        "installer/Install-EwP.ps1",
        "installer/Remove-EwP.ps1",
        "installer/Install-EwP.sh",
        "installer/bootstrap.ps1.in",
        "installer/bootstrap.sh.in",
        "scripts/setup-windows.ps1",
        "scripts/repair-dependencies.sh",
        "scripts/install-fresh-ubuntu.sh",
        "scripts/setup-models.sh",
    ]
    for rel in script_files:
        source = (ROOT / rel).read_text()
        inputs[rel] = digest(source)
        # Inventory all quoted prose (including printf arguments spread across lines).
        pattern = r"'([^'\n]*)'|\"((?:\\.|[^\"\n])*)\""
        for match in re.finditer(pattern, source):
            value = match.group(1) if match.group(1) is not None else match.group(2)
            if not re.search("[A-Za-z]{3}", value) or not (" " in value or value.endswith("?")):
                continue
            if any(
                marker in value
                for marker in [
                    "Join-Path",
                    "@(",
                    "os.environ",
                    "import ",
                    "$bootstrap_",
                    "exec ",
                    " --",
                    "Path=",
                    "${PATH",
                    "@echo",
                    "if(",
                    "raise SystemExit",
                ]
            ):
                continue
            if value.startswith(("-", "${", "$env:", "$(", "export ")):
                continue
            if value.startswith('printf "'):
                nested = re.match(r'printf "((?:\\.|[^"\\])*)"', value)
                if nested:
                    value = nested.group(1)
            value = value.replace(r"\n", "\n").replace(r"\t", "\t")
            en, pl = value, value
            if " / " in value and any(word in value for word in ["Usunac", "Nacisnij"]):
                en, pl = value.split(" / ", 1)
            add(
                "Raport_i_terminal",
                en,
                pl,
                f"Terminal / {Path(rel).name}",
                f"{rel}:{source.count(chr(10), 0, match.start()) + 1}",
                (
                    "Tekst oryginalny skryptu. Zachowaj %s, nazwy polec"
                    "eń i zmienne $…; komunikaty narzędzi zewnętrznych "
                    "nie należą do tej listy."
                ),
                parameters=", ".join(
                    sorted(set(re.findall(r"%[sd]|\$\{[^}]+\}|\$[A-Za-z_]\w*", value)))
                ),
            )
            binding_count["script-prose"] += 1

    for value, context in [
        ("Text (*.txt)|*.txt", "Filtr okna zapisu raportu"),
        ("yyyyMMdd-HHmmss-fff-zzz", "Kod daty w nazwie raportu; +01:00 zostaje +0100"),
        ("HH:mm:ss.fff zzz", "Znacznik czasu w dzienniku"),
        ("hh:mm:ss", "Czas operacji / ETA"),
        ("GB", "Dziesiętne GB (1 GB = 10^9 B)"),
        ("MB/s", "Prędkość pobierania"),
        ("HF_HTTP_{status}", "Kod odpowiedzi HF"),
        ("OR_HTTP_{status}", "Kod odpowiedzi OR"),
    ]:
        add(
            "Dane_i_formaty",
            value,
            value,
            context,
            "installer/windows",
            (
                "Stała techniczna lub format; nie tłumaczyć składni"
                ". Uwagi można wpisać w kolumnie obok."
            ),
            decision="NIE ZMIENIAĆ",
        )
    models = json.loads((ROOT / "installer/models.json").read_text())["models"]
    for model in models:
        add(
            "Dane_i_formaty",
            model["repository"],
            model["repository"],
            "Nazwa modelu — " + model["code"],
            "installer/models.json",
            (
                "Identyfikator repozytorium, nie nazwa do tłumaczen"
                "ia. Opcjonalny / zainstalowany są osobnymi tekstam"
                "i."
            ),
            decision="NIE ZMIENIAĆ",
            key=model["code"],
        )

    # Exact notices shipped in the final installer, not development/private source registers.
    legal_manifest = []
    with zipfile.ZipFile(bundle) as archive:
        names = [
            n
            for n in archive.namelist()
            if n.startswith("licenses/")
            or n.endswith(
                (
                    "/LICENSE",
                    "/LICENSING.md",
                    "/LICENSE-ASSETS.txt",
                    "/NOTICE.txt",
                    "/Lucide-LICENSE.txt",
                    "/Montserrat-OFL.txt",
                    "/NotoSansMono-OFL.txt",
                )
            )
        ]
        notice_files = {name: archive.read(name) for name in names}
    for name, content in notice_files.items():
        text = content.decode("utf-8-sig")
        project = name.endswith(("LICENSING.md", "LICENSE-ASSETS.txt", "NOTICE.txt"))
        sheet = "Notices_projektu" if project else "Oryginalne_licencje"
        paragraphs = [p for p in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if p.strip()]
        if name.endswith("/NOTICE.txt"):
            paragraphs = re.split(
                (
                    " (?=Rights holder:|English:|Creator URL:|See LICEN"
                    "SE-ASSETS|Fonts:|Icons:|Assets copied)"
                ),
                " ".join(text.split()),
            )
        occurrences = Counter()
        for index, paragraph in enumerate(paragraphs, 1):
            # No truncation: unusually long upstream paragraphs get lossless cell-sized chunks.
            chunks = [paragraph[n : n + 1400] for n in range(0, len(paragraph), 1400)]
            for chunk_index, chunk in enumerate(chunks, 1):
                occurrences[chunk] += 1
                note = (
                    "Treść projektu w aktualnym pakiecie; obecnie EN ró"
                    "wnież w polskiej wersji. Propozycje wpisz w EN/PL;"
                    " oryginał zostaje zachowany."
                )
                if not project:
                    note = (
                        "Oryginał licencji/autorstwa dostawcy — zachować be"
                        "z zmian. Do uwag służy kolumna obok; polski tekst "
                        "objaśniający nie zastępuje licencji."
                    )
                flags = []
                for pattern, flag in [
                    ("TODO", "komentarz TODO"),
                    ("placeholder", "niezweryfikowany adres twórcy"),
                    ("Assets copied", "wewnętrzna historia plików"),
                    ("brandbook", "odniesienie do prywatnych materiałów"),
                    ("Do not invent", "instrukcja dla projektu"),
                    ("Review draft assets", "instrukcja produkcyjna"),
                    ("post-processing", "opis API może pomijać chmurową transkrypcję"),
                ]:
                    if pattern in chunk:
                        flags.append(flag)
                if flags:
                    note += " DO OCENY: " + "; ".join(flags) + "."
                key = name + "\0" + chunk + "\0" + str(occurrences[chunk])
                add(
                    sheet,
                    chunk,
                    context=Path(name).name
                    + f" / akapit {index}"
                    + (f" / część {chunk_index}" if len(chunks) > 1 else ""),
                    location="pakiet0.24.2!" + name,
                    notes=note,
                    decision="DO OCENY" if project else "ORYGINAŁ",
                    key=key,
                )
        legal_manifest.append(
            {
                "path": name,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "paragraphs": len(paragraphs),
                "project_copy": project,
            }
        )

    for old in historical:
        if old["ID"] not in preserved:
            row = add(
                "Archiwum_ID",
                old["EN"],
                old["PL"],
                old["Context"],
                "installer/ui-en-pl.csv",
                (
                    "Stary pomocniczy wpis niewystępujący w aktualnej p"
                    "arze T(). Zachowany do mapowania ID; nie traktować"
                    " jako aktualny ekran."
                ),
                decision="ARCHIWUM",
                key=old["ID"],
            )
            row["ID"] = old["ID"]
    ids = [r["ID"] for r in rows]
    assert len(ids) == len(set(ids)), "Duplicate stable IDs"
    assert {r["ID"] for r in historical}.issubset(ids), "Lost historical IDs"
    assert all(c["classification"] for c in coverage)
    manifest = {
        "baseline_source": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "product_version": "0.24.2",
        "sheet_counts": dict(Counter(r["sheet"] for r in rows)),
        "total_rows": len(rows),
        "historical_ids": len(historical),
        "retained_active_historical_ids": len(preserved),
        "cs_literal_count": len(coverage),
        "bindings": dict(binding_count),
        "all_csharp_literals_classified": True,
        "ui_pair_occurrences": len(ui_pairs),
        "input_sha256": inputs,
        "legal_files": legal_manifest,
    }
    return rows, manifest, coverage, notice_files


def workbook(rows, manifest, output):
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Protection
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.worksheet.table import Table, TableStyleInfo

    book = Workbook()
    start = book.active
    start.title = "Start"
    instructions = [
        ["EwP Transcripts — komplet tekstów instalatora EN / PL"],
        ["Baza", "Instalator 0.24.2; źródło produktu 7178bc7; tabela źródeł w coverage.json."],
        [
            "Jak poprawiać",
            (
                "Edytuj EN i PL. Porównamy wartości przed i po po ID. "
                "Kolumna Decyzja nie jest wymagana; uwagi są opcjonalne."
            ),
        ],
        [
            "Identyfikatory",
            (
                "Nie zmieniaj ID. Zachowaj nazwy parametrów {…}, ko"
                "dy błędów, nazwy własne i końcowe spacje we fragme"
                "ntach."
            ),
        ],
        [
            "Od czego zacząć",
            (
                "Interfejs: etykiety i komunikaty. Pelne_komunikaty"
                ": całe zdania składane w programie; pomocne zwłasz"
                "cza przy opisach miejsca na dysku."
            ),
        ],
        [
            "Pełny tekst a fragment",
            (
                "Jeśli zmienisz całe zdanie w Pelne_komunikaty, nie"
                " musisz jednocześnie poprawiać każdego fragmentu. "
                "Rozbieżności rozstrzygniemy przy integracji."
            ),
        ],
        [
            "EN również w PL",
            (
                "Identyczny tekst EN/PL w raporcie, terminalu lub n"
                "otices oznacza obecny brak lokalizacji, a nie goto"
                "we polskie tłumaczenie."
            ),
        ],
        [
            "Notices_projektu",
            (
                "Informacje projektu i warunki assetów; zaznaczono "
                "TODO, adresy placeholder i komentarze wewnętrzne. "
                "Propozycje nie zmieniają jeszcze programu/licencji"
                "."
            ),
        ],
        [
            "Oryginalne_licencje",
            (
                "Pełne oryginały z pakietu podzielone na akapity; z"
                "achowaj ich brzmienie. Uwagi wpisuj obok. Dokładne"
                " pliki są też w katalogu oryginalne-notices."
            ),
        ],
        [
            "Linki / Dane_i_formaty",
            (
                "Kontekst linków, formatów czasu, jednostek i nazw "
                "modeli. Zmienne i składnia nie są zwykłymi etykiet"
                "ami."
            ),
        ],
        [
            "Archiwum_ID",
            (
                "Dawne wpisy pomocniczego CSV, zachowane dla mapowa"
                "nia identyfikatorów; nie są aktualną kopią ekranu."
            ),
        ],
        [
            "Zakres kompletności",
            (
                "Własne teksty stałe instalatora/maintenance, skryp"
                "tów i raportu, dynamiczne szablony oraz 12 plików n"
                "otices z pakietu. Zmienny stderr narzędzi zewnętrz"
                "nych i komunikaty Windows nie mają zamkniętej list"
                "y."
            ),
        ],
        [
            "Po korekcie",
            (
                "Zapisz i odeślij XLSX. Alternatywnie CSV (UTF-8, s"
                "eparator średnik) z tymi samymi ID. Nic nie został"
                "o jeszcze zastosowane w programie."
            ),
        ],
        [
            "Dotychczasowe ustalenia",
            (
                "Bez nowego retestu manualnego. Zatwierdzona tabela"
                " interfejsu aplikacji i poprzednie instalatory poz"
                "ostają bez zmian."
            ),
        ],
        ["Liczba wpisów", manifest["total_rows"]],
    ]
    for values in instructions:
        start.append(values)
    start.merge_cells("A1:B1")
    start.column_dimensions["A"].width = 29
    start.column_dimensions["B"].width = 118
    start.freeze_panes = "B3"
    for row in start:
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.font = Font(name="Calibri", size=11)
        start.row_dimensions[row[0].row].height = 44 if row[0].row > 2 else 28
    start["A1"].font = Font(name="Calibri", size=16, bold=True, color="355880")
    start.row_dimensions[1].height = 32
    baseline = book.create_sheet("_oryginal")
    baseline.append(["Arkusz", *COLUMNS])
    for row in rows:
        baseline.append([row["sheet"], *[row[c] for c in COLUMNS]])
    baseline.sheet_state = "hidden"
    for sheet_index, name in enumerate(SHEETS, 1):
        ws = book.create_sheet(name)
        ws.append(COLUMNS)
        selected = [r for r in rows if r["sheet"] == name]
        if name not in {"Notices_projektu", "Oryginalne_licencje"}:
            selected.sort(
                key=lambda r: [
                    int(part) if part.isdigit() else part
                    for part in re.split(r"(\d+)", r["Kontekst"])
                ]
            )
        for record in selected:
            ws.append([record[c] for c in COLUMNS])
        widths = [31, 25, 42, 76, 76, 18, 72, 36, 76, 76, 76]
        for index, width in enumerate(widths, 1):
            ws.column_dimensions[
                __import__("openpyxl").utils.get_column_letter(index)
            ].width = width
        ws.column_dimensions["J"].hidden = ws.column_dimensions["K"].hidden = True
        ws.freeze_panes = "D2"
        ws.sheet_view.zoomScale = 75
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_title_rows = "1:1"
        ws.print_options.horizontalCentered = True
        ws.print_area = f"A1:I{ws.max_row}"
        ws.sheet_properties.tabColor = (
            "355880" if sheet_index < 4 else "3A7366" if name == "Notices_projektu" else "687887"
        )
        for cells in ws:
            for cell in cells:
                # Store every source string as text, never an executable spreadsheet formula.
                if isinstance(cell.value, str):
                    cell.data_type = "s"
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                cell.font = Font(name="Calibri", size=11)
                cell.protection = Protection(locked=cell.column not in {4, 5, 6, 7})
                if cell.row == 1:
                    cell.fill = PatternFill("solid", fgColor="355880")
                    cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                elif cell.column in {4, 5}:
                    cell.fill = PatternFill(
                        "solid",
                        fgColor="FFF6D9"
                        if name not in {"Oryginalne_licencje", "Dane_i_formaty", "Archiwum_ID"}
                        else "EDF0F2",
                    )
                elif cell.column in {6, 7}:
                    cell.fill = PatternFill("solid", fgColor="E8F4ED")
            if cells[0].row > 1:
                estimate = max(
                    sum(
                        max(1, (len(line) + 74) // 75) for line in str(cell.value or "").split("\n")
                    )
                    for cell in cells[3:7]
                )
                ws.row_dimensions[cells[0].row].height = min(400, max(44, estimate * 15 + 12))
        ws.row_dimensions[1].height = 32
        if selected:
            table = Table(displayName=f"Copy{sheet_index}", ref=f"A1:K{ws.max_row}")
            table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=False)
            ws.add_table(table)
            validation = DataValidation(
                type="list",
                formula1=(
                    '"DO KOREKTY,DO OCENY,ZMIANA,BEZ ZMIAN,USUNĄĆ,PYTAN'
                    'IE,ORYGINAŁ,NIE ZMIENIAĆ,ARCHIWUM"'
                ),
            )
            ws.add_data_validation(validation)
            validation.add(f"F2:F{ws.max_row}")
    book.properties.creator = "EwP Transcripts"
    book.properties.lastModifiedBy = "EwP Transcripts"
    book.properties.title = "Komplet tekstów instalatora EN/PL — korekta"
    path = output / "EwP-instalator-EN-PL-do-korekty-2026-11-25.xlsx"
    book.save(path)
    # Validate actual written cells, formatting, baseline and formula exclusion via a second read.
    loaded = load_workbook(path)
    assert loaded["_oryginal"].sheet_state == "hidden"
    seen = {}
    for name in SHEETS:
        ws = loaded[name]
        assert ws.freeze_panes == "D2" and len(ws.tables) == 1
        for values in ws.iter_rows(min_row=2, values_only=True):
            seen[values[0]] = values
        assert all(cell.data_type != "f" for row in ws for cell in row)
    assert len(seen) == len(rows)
    for record in rows:
        values = seen[record["ID"]]
        assert values[3] == record["EN"] and values[4] == record["PL"]
        assert values[9] == record["EN oryginał"] and values[10] == record["PL oryginał"]
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a new review directory; previous workbooks must remain immutable")
    args.output.mkdir(parents=True)
    rows, manifest, coverage, notices = inventory(args.bundle)
    original_dir = args.output / "oryginalne-notices"
    for name, content in notices.items():
        target = original_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    csv_path = args.output / "EwP-instalator-EN-PL-do-korekty.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["Arkusz", *COLUMNS], delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({"Arkusz": row["sheet"], **{key: row[key] for key in COLUMNS}})
    csv_rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig", newline=""), delimiter=";"))
    assert len(csv_rows) == len(rows)
    assert all(
        csv_row["EN"] == row["EN"] and csv_row["PL"] == row["PL"]
        for csv_row, row in zip(csv_rows, rows, strict=True)
    )
    xlsx = workbook(rows, manifest, args.output)
    manifest["outputs"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [xlsx, csv_path]
    }
    manifest["source_bundle_sha256"] = hashlib.sha256(args.bundle.read_bytes()).hexdigest()
    manifest["app_workbook_sha256"] = hashlib.sha256(
        (ROOT / "docs/ui-language/ewp-ui-en-pl-review-2026-11-22.xlsx").read_bytes()
    ).hexdigest()
    (args.output / "coverage.json").write_text(
        json.dumps({**manifest, "csharp_literals": coverage}, indent=2, ensure_ascii=False) + "\n"
    )
    preview = []
    for sheet in SHEETS:
        preview.append(
            "<h2>"
            + html.escape(sheet)
            + "</h2><table><tr><th>ID / kontekst</th><th>EN</th><th>PL</th><th>Uwagi</th></tr>"
        )
        for row in [r for r in rows if r["sheet"] == sheet]:
            preview.append(
                "<tr>"
                + "".join(
                    "<td>" + html.escape(value).replace("\n", "<br>") + "</td>"
                    for value in [
                        row["ID"] + "\n" + row["Kontekst"],
                        row["EN"],
                        row["PL"],
                        row["Uwagi do korekty"],
                    ]
                )
                + "</tr>"
            )
        preview.append("</table>")
    (args.output / "podglad.html").write_text(
        (
            '<!doctype html><html lang="pl"><meta charset="utf-'
            '8"><title>EwP — teksty instalatora</title><style>b'
            "ody{font:15px system-ui;margin:2rem;color:#1c3543}"
            "table{border-collapse:collapse;table-layout:fixed;"
            "width:100%}td,th{border:1px solid #bbccd7;padding:"
            ".6rem;vertical-align:top;overflow-wrap:anywhere}th"
            "{background:#355880;color:white}td{white-space:nor"
            "mal}h2{margin-top:3rem}</style><h1>Komplet tekstów"
            " instalatora EN/PL</h1><p>Podgląd do czytania. Kor"
            "ekty wpisz w XLSX lub CSV. Liczba wpisów: "
        )
        + str(len(rows))
        + ".</p>"
        + "".join(preview)
        + "</html>"
    )
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in [
                    "total_rows",
                    "sheet_counts",
                    "historical_ids",
                    "retained_active_historical_ids",
                    "cs_literal_count",
                    "bindings",
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
