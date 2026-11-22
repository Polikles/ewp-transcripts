"""Export the effective GUI copy and its provenance for an editable EN/PL review.

Optional tooling only: openpyxl, tree-sitter, tree-sitter-javascript and a Node executable.
No app, browser, provider, credentials or private runtime data are opened by this exporter.
The generated workbook stays outside the repository until owner review.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/ewp_transcripts/web_assets"
LOCALES = [ASSETS / "ui_locale.js", ASSETS / "ui_locale_catalog.js"]
VM = r"""
const fs=require('fs'),vm=require('vm');
const input=JSON.parse(fs.readFileSync(0,'utf8')),context=vm.createContext({});
for(const source of input.sources)vm.runInContext(source,context);
vm.runInContext('guiLocale="pl";',context);
context.input=input;
const result=vm.runInContext(`({
  exact:[...guiPolish],errors:[...guiPolishErrorDescriptions],
  literals:input.literals.map(raw=>eval(raw)),
  translations:input.texts.map(text=>guiUiText(text))
})`,context);
process.stdout.write(JSON.stringify(result));
"""


def run_locale(node, literals=(), texts=()):
    payload = {
        "sources": [p.read_text() for p in LOCALES],
        "literals": list(literals),
        "texts": list(texts),
    }
    return json.loads(
        subprocess.run(
            [str(node), "-e", VM],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        ).stdout
    )


def walk(node):
    yield node
    for child in node.named_children:
        yield from walk(child)


def text(node):
    return node.text.decode()


def reference(path, line):
    return f"{path.relative_to(ROOT).as_posix()}:{line}"


class HtmlCopy(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append((tag, attrs.get("id", "")))
        for attribute in ("title", "aria-label", "placeholder", "alt"):
            if attrs.get(attribute):
                self.items.append((attrs[attribute], f"#{attrs.get('id', tag)} @{attribute}"))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if not any(tag in {"style", "script", "pre", "code"} for tag, _ in self.stack):
            ids = [identifier for _, identifier in self.stack if identifier]
            self.items.append((data, "#" + ids[-1] if ids else "HTML text"))


def human(value):
    if value in {"use strict", "Content-Type", "Content-Length"}:
        return False
    if not value.strip() or len(value) > 8000:
        return False
    if re.search(r"https?://|=>|querySelector|[{}][;]|^[/#.][\w./#-]+$", value):
        return False
    return bool(re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}|^[A-Z][a-z]+[.!…:]?$", value))


def template(node):
    parts, substitutions, at = [], {}, 1
    for child in node.named_children:
        if child.type == "template_substitution":
            expression = text(child)[2:-1]
            expression_node = child.named_children[0] if child.named_children else None
            if expression_node and expression_node.type == "ternary_expression":
                branches = [
                    expression_node.child_by_field_name(key)
                    for key in ("consequence", "alternative")
                ]
                if all(branch is not None and branch.type == "string" for branch in branches):
                    # Plural suffix branches are wording, rather than a runtime placeholder.
                    parts.append(text(branches[1])[1:-1])
                    continue
            name = re.sub(r"[^A-Za-z0-9_]+", "_", expression).strip("_")
            if not name or len(name) > 35:
                name = f"value_{at}"
            token = "{" + name + "}"
            substitutions[token] = expression
            parts.append(token)
            at += 1
        elif child.type in {"string_fragment", "escape_sequence"}:
            parts.append(text(child))
    value = "".join(parts).replace(r"\n", "\n").replace(r"\t", "\t")
    return value, substitutions


def regex_template(pattern):
    """Create a readable template from a replacement rule, retaining its original regex metadata."""
    value = pattern
    if value.startswith("/"):
        value = value[1 : value.rfind("/")]
    value = value.removeprefix("^").removesuffix("$")
    group, index, out = 0, 0, []
    while index < len(value):
        if value[index] == "(" and not value.startswith("(?:", index):
            end, depth, escaped = index + 1, 1, False
            while end < len(value) and depth:
                char = value[end]
                if not escaped:
                    depth += char == "("
                    depth -= char == ")"
                escaped = char == "\\" and not escaped
                end += 1
            group += 1
            out.append("{value_" + str(group) + "}")
            index = end
            continue
        if value[index] == "\\" and index + 1 < len(value):
            next_char = value[index + 1]
            if next_char in "sw":
                out.append(" " if next_char == "s" else "{value}")
                index += 2
                if index < len(value) and value[index] in "*+?":
                    index += 1
            else:
                out.append(next_char)
                index += 2
        elif value[index] == "?":
            index += 1
        else:
            out.append(value[index])
            index += 1
    return "".join(out)


def collect(node):
    import tree_sitter
    import tree_sitter_javascript

    parser = tree_sitter.Parser(tree_sitter.Language(tree_sitter_javascript.language()))
    exact = dict(run_locale(node)["exact"])
    copies, recipes, raw_literals, direct_rules = [], [], [], []
    js_paths = sorted(ASSETS.glob("*.js"))
    for path in js_paths:
        bindings = {}
        tree = parser.parse(path.read_bytes())
        assert not tree.root_node.has_error, path
        for n in walk(tree.root_node):
            source = reference(path, n.start_point.row + 1)
            if path not in LOCALES and n.type == "string":
                raw_literals.append((text(n), source, text(n.parent)[:100]))
            elif path not in LOCALES and n.type == "template_string":
                value, tokens = template(n)
                copies.append(
                    (value, source, "JS template", {"template": text(n), "tokens": tokens})
                )
            if path in LOCALES:
                ancestor = n
                scope = "global"
                while ancestor is not None:
                    if ancestor.type == "function_declaration":
                        scope = text(ancestor.child_by_field_name("name"))
                        break
                    ancestor = ancestor.parent
                if n.type == "ternary_expression" and "guiLocale" in text(
                    n.child_by_field_name("condition")
                ):
                    yes, no = [n.child_by_field_name(k) for k in ("consequence", "alternative")]
                    if yes.type == no.type == "string":
                        pl, en = run_locale(node, literals=[text(yes), text(no)])["literals"]
                        owner = n.parent
                        while owner and owner.type != "ternary_expression":
                            owner = owner.parent
                        field = re.search(r'\.id\s*===\s*"([^"]+)"', text(owner)) if owner else None
                        if field:
                            direct_rules.append(
                                (
                                    en,
                                    pl,
                                    {
                                        "pattern": "#" + field[1],
                                        "scope": "field",
                                        "field": field[1],
                                        "source": source,
                                    },
                                )
                            )
                if n.type == "variable_declarator":
                    name = n.child_by_field_name("name")
                    value = n.child_by_field_name("value")
                    if name and value:
                        patterns = [text(c) for c in walk(value) if c.type == "regex"]
                        if patterns:
                            bindings[text(name)] = patterns[0]
                if n.type == "return_statement" and n.named_children:
                    returned = n.named_children[0]
                    if returned.type == "template_string":
                        for name, pattern in bindings.items():
                            if re.search(r"\b" + re.escape(name) + r"\[\d+\]", text(returned)):
                                value, tokens = template(returned)
                                for token, expression in tokens.items():
                                    group = re.search(re.escape(name) + r"\[(\d+)\]", expression)
                                    if group:
                                        value = value.replace(token, "{value_" + group[1] + "}")
                                direct_rules.append(
                                    (
                                        regex_template(pattern),
                                        value,
                                        {
                                            "pattern": pattern,
                                            "scope": scope,
                                            "source": source,
                                            "replacement": text(returned),
                                        },
                                    )
                                )
                                break
                    elif returned.type == "string" and scope == "guiPolishFallbackError":
                        direct_rules.append(
                            (
                                "{code}: {message}",
                                run_locale(node, literals=[text(returned)])["literals"][0],
                                {
                                    "pattern": text(n.parent.child_by_field_name("condition"))
                                    if n.parent.type == "if_statement"
                                    else "default",
                                    "scope": scope,
                                    "source": source,
                                    "replacement": text(returned),
                                },
                            )
                        )
                if (
                    n.type == "array"
                    and len(n.named_children) == 2
                    and n.named_children[0].type == "regex"
                ):
                    recipes.append(
                        (text(n.named_children[0]), text(n.named_children[1]), source, scope)
                    )
                if n.type == "call_expression":
                    function = n.child_by_field_name("function")
                    arguments = n.child_by_field_name("arguments")
                    children = arguments.named_children if arguments else []
                    if (
                        function
                        and text(function).endswith(".replace")
                        and len(children) == 2
                        and children[0].type == "regex"
                    ):
                        recipes.append((text(children[0]), text(children[1]), source, scope))
    decoded = run_locale(node, literals=[r[0] for r in raw_literals])["literals"]
    for value, (_, source, parent) in zip(decoded, raw_literals, strict=True):
        copies.append((value, source, parent, {}))
    # Server HTML and error/diagnostic descriptions, including formatted message templates.
    for path in sorted((ROOT / "src/ewp_transcripts").rglob("*.py")):
        if path.name == "cli.py":
            continue
        source_text = path.read_text()
        tree = ast.parse(source_text)
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        for n in ast.walk(tree):
            value, recipe = "", {}
            parent = parents.get(n)
            if (
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and not isinstance(parent, ast.JoinedStr)
            ):
                value = n.value
            elif isinstance(n, ast.JoinedStr):
                fragments = []
                for child in n.values:
                    if isinstance(child, ast.Constant):
                        fragments.append(str(child.value))
                    else:
                        expression = ast.unparse(child.value)
                        fragments.append(
                            "{" + re.sub(r"[^A-Za-z0-9_]+", "_", expression).strip("_") + "}"
                        )
                value = "".join(fragments)
                recipe = {"python_template": ast.get_source_segment(source_text, n)}
            if not value:
                continue
            # Exclude Python docstrings, developer log strings and schema/technical field values.
            if isinstance(parent, ast.Expr) or (
                isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Attribute)
                and parent.func.attr in {"debug", "info", "warning", "error", "exception"}
            ):
                continue
            visible_module = path.name.startswith("web_") or path.name in {
                "gui_dependencies.py",
                "gui_library.py",
                "doctor.py",
            }
            is_error = isinstance(parent, ast.Call) and (
                isinstance(parents.get(parent), ast.Raise)
                or re.search("Error|Issue|Diagnostic", ast.unparse(parent.func))
            )
            if visible_module or is_error or value in exact:
                copies.append(
                    (
                        value,
                        reference(path, n.lineno),
                        "backend diagnostic" if visible_module else "backend detail",
                        recipe,
                    )
                )
    clean, origins, metadata = {}, defaultdict(set), defaultdict(list)

    def add(value, source, context, recipe):
        value = html.unescape(value).strip()
        if value in exact or human(value):
            clean[value] = True
            origins[value].add(source + " · " + context)
            if recipe and recipe not in metadata[value]:
                metadata[value].append(recipe)

    for value, source, context, recipe in copies:
        if re.search(
            r"</?(?:div|span|p|button|label|legend|fieldset|h[1-6]|section|option|a|strong|details|summary|input|ul|ol|li|table|th|td)\b[^>]*>",
            value,
        ):
            parsed = HtmlCopy()
            parsed.feed(value)
            for fragment, where in parsed.items:
                add(fragment, source, where, recipe)
        else:
            add(value, source, context, recipe)
    # Locale fallbacks/templates not represented by exact English keys still need review.
    rules = direct_rules
    replacements = [r[1] for r in recipes if r[1].startswith(('"', "'"))]
    decoded_replacements = iter(run_locale(node, literals=replacements)["literals"])
    for pattern, replacement, source, scope in recipes:
        pl = next(decoded_replacements) if replacement.startswith(('"', "'")) else ""
        if pl:
            en = regex_template(pattern)
            pl = re.sub(r"\$(\d+)", lambda m: "{value_" + m[1] + "}", pl)
            rules.append(
                (
                    en,
                    pl,
                    {
                        "pattern": pattern,
                        "replacement": replacement,
                        "source": source,
                        "scope": scope,
                    },
                )
            )
    return exact, clean, origins, metadata, rules


def translated_templates(node, english):
    """Let the real formatter handle numeric placeholders, then restore their editable names."""
    samples, substitutions = [], []
    for en in english:
        tokens = list(dict.fromkeys(re.findall(r"\{[A-Za-z0-9_]+\}", en)))
        values = {token: str(9876000 + i) for i, token in enumerate(tokens)}
        sample = en
        for token, value in values.items():
            sample = sample.replace(token, value)
        samples.append(sample)
        substitutions.append(values)
    result = run_locale(node, texts=samples)["translations"]
    for index, values in enumerate(substitutions):
        for token, value in values.items():
            result[index] = result[index].replace(value, token)
    return result


def main():
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.resolve().is_relative_to(ROOT), "Keep the initial review outside repo"
    assert not args.output.exists(), "Never overwrite an owner-edited workbook"
    exact, copies, origins, metadata, rules = collect(args.node)
    english = sorted(set(exact) | set(copies))
    translated = translated_templates(args.node, english)
    rows = []
    for en, pl in zip(english, translated, strict=True):
        active = en in copies
        kind = "template" if "{" in en else "text"
        section = "Templates" if kind == "template" else "UI" if active else "Other catalog"
        status = "Current copy" if pl != en else "Same EN/PL — check"
        if not active:
            status = "Catalog entry; not found in current UI literals"
        if any("backend diagnostic" in s for s in origins[en]):
            section = "Diagnostics"
        elif any("backend detail" in s for s in origins[en]):
            section = "Backend details"
            status = "Technical detail; may remain English in JSON"
        key = kind + ":" + en
        identifier = "ui." + hashlib.sha256(key.encode()).hexdigest()[:16]
        rows.append(
            {
                "ID": identifier,
                "EN": en,
                "PL": pl,
                "Context": "\n".join(sorted(origins[en])),
                "Review": status,
                "Notes": "",
                "section": section,
                "kind": kind,
                "metadata": metadata[en],
            }
        )
    seen = set()
    for en, pl, recipe in rules:
        key = recipe["pattern"] + "\0" + recipe["scope"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "ID": (
                    "field." + recipe["field"] + ".text"
                    if "field" in recipe
                    else "rule." + hashlib.sha256(key.encode()).hexdigest()[:16]
                ),
                "EN": en,
                "PL": pl,
                "Context": recipe["source"],
                "Review": "Dynamic replacement template",
                "Notes": "",
                "section": "UI" if "field" in recipe else "Templates",
                "kind": "rule",
                "metadata": [recipe],
            }
        )
    # Error-code fallbacks are visible copy even when their detailed body varies by failure.
    error_descriptions = run_locale(args.node)["errors"]
    for code, pl in error_descriptions:
        rows.append(
            {
                "ID": "error." + code,
                "EN": code + ": {message}",
                "PL": code + ": " + pl,
                "Context": "Error-code fallback; detailed bodies are also listed in Diagnostics",
                "Review": "Keep error code unchanged",
                "Notes": "",
                "section": "Diagnostics",
                "kind": "error-code",
                "metadata": [{"code": code}],
            }
        )
    guides = json.loads((ASSETS / "guides/index.json").read_text())

    def guide_values(value, path):
        if isinstance(value, dict):
            if "en" in value and "pl" in value:
                rows.append(
                    {
                        "ID": "guide." + path,
                        "EN": value["en"],
                        "PL": value["pl"],
                        "Context": "guides/index.json · " + path,
                        "Review": "Quick guide copy",
                        "Notes": "",
                        "section": "Quick guides",
                        "kind": "guide",
                        "metadata": [{"path": path}],
                    }
                )
            else:
                for key, item in value.items():
                    guide_values(item, path + "." + key if path else key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                guide_values(item, path + "." + str(index))

    guide_values(guides, "")
    workbook = Workbook()
    readme = workbook.active
    readme.title = "Read first"
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    fingerprint = hashlib.sha256()
    source_paths = sorted((ROOT / "src/ewp_transcripts").rglob("*.py"))
    source_paths += sorted(ASSETS.glob("*.js")) + [ASSETS / "guides/index.json"]
    for path in source_paths:
        fingerprint.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes())
    source_digest = fingerprint.hexdigest()
    instructions = [
        (
            "EN–PL interface review",
            "Edytuj kolumny EN i PL. Możesz poprawiać oba języki; Notes służy do uwag.",
        ),
        (
            "ID",
            "Nie zmieniaj ID, nazw arkuszy ani nagłówków. Nie usuwaj wierszy; "
            "niepożądany tekst opisz w Notes.",
        ),
        (
            "Placeholders",
            "Zachowaj znaczniki {nazwa}, {value_1}, kody GUI_… i SPEECH_… oraz "
            "identyfikatory techniczne. Zmieniaj otaczające zdania.",
        ),
        (
            "Shared text",
            "Jeden napis użyty w kilku miejscach ma wspólny ID; Context podaje "
            "pliki/pola. Jeśli miejsca wymagają różnych nazw, opisz to w Notes.",
        ),
        (
            "Templates",
            "Templates zawiera szablony z wartościami zmiennymi. Wiersze rule.* "
            "odpowiadają regułom formatowania, nie są przykładowymi wynikami "
            "transkrypcji.",
        ),
        (
            "Diagnostics",
            "Diagnostics zawiera błędy/opisy i komunikaty zapasowe. {message} oznacza "
            "szczegółowy komunikat zależny od przyczyny.",
        ),
        (
            "Other catalog",
            "Other catalog zawiera pozostałe wpisy katalogu, także historyczne lub "
            "rzadko używane. Są osobno, żeby nie mieszać ich z bieżącymi polami.",
        ),
        (
            "Backend details",
            "Backend details to szczegółowe komunikaty techniczne, często widoczne tylko w JSON. "
            "Mogą pozostać po angielsku; nie są dodatkowymi krokami workflow.",
        ),
        (
            "Missing translation",
            "Same EN/PL — check oznacza, że obecnie oba języki pokazują ten sam tekst. "
            "To może być brak tłumaczenia albo nazwa własna.",
        ),
        (
            "Documentation",
            "Quick guides to krótkie instrukcje w GUI. Pełne podręczniki EN/PL będą "
            "opracowane dopiero po zatwierdzeniu napisów.",
        ),
        (
            "Return",
            "Zapisz zmieniony XLSX i przekaż go z powrotem. Ukryty arkusz _baseline "
            "zachowuje oryginały do porównania; nie edytuj go.",
        ),
        ("Baseline", baseline),
        ("Source SHA256", source_digest),
        (
            "Scope",
            "Bieżące literały UI, efektywny katalog tłumaczeń, szablony dynamiczne, "
            "komunikaty backendu, błędy i krótkie instrukcje. Bez danych nagrań i "
            "kluczy.",
        ),
        (
            "External messages",
            "Komunikaty systemu operacyjnego i dostawców API nie mają stałej treści. "
            "Arkusz obejmuje napisy programu, nie cudze odpowiedzi ani transkrypcje.",
        ),
    ]
    for record in instructions:
        readme.append(record)
    readme.column_dimensions["A"].width = 25
    readme.column_dimensions["B"].width = 110
    for row in readme:
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        readme.row_dimensions[row[0].row].height = 45
    headers = ["ID", "EN", "PL", "Context", "Review", "Notes"]
    for section in [
        "UI",
        "Templates",
        "Diagnostics",
        "Quick guides",
        "Other catalog",
        "Backend details",
    ]:
        sheet = workbook.create_sheet(section)
        sheet.append(headers)
        for row in sorted(
            (r for r in rows if r["section"] == section), key=lambda r: r["Context"] + r["EN"]
        ):
            sheet.append([row[h] for h in headers])
        sheet.freeze_panes = "B2"
        sheet.auto_filter.ref = sheet.dimensions
        for name, width in {"A": 31, "B": 70, "C": 70, "D": 45, "E": 25, "F": 45}.items():
            sheet.column_dimensions[name].width = width
        for row in sheet:
            for cell in row:
                cell.data_type = "s"  # Never turn copy beginning with =, +, - or @ into formulas.
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            if row[0].row == 1:
                for cell in row:
                    cell.fill = PatternFill("solid", fgColor="22354A")
                    cell.font = Font(color="FFFFFF", bold=True)
            else:
                for cell in row[1:3]:
                    cell.fill = PatternFill("solid", fgColor="FFF5D6")
                max_lines = max(
                    len(str(c.value or "")) // 65 + str(c.value or "").count("\n") + 1
                    for c in row[1:3]
                )
                sheet.row_dimensions[row[0].row].height = min(180, max(32, max_lines * 16))
    baseline_sheet = workbook.create_sheet("_baseline")
    baseline_sheet.sheet_state = "hidden"
    baseline_sheet.append(["ID", "EN", "PL", "section", "kind", "metadata"])
    for row in rows:
        baseline_sheet.append(
            [
                row[k] if k != "metadata" else json.dumps(row[k], ensure_ascii=False)
                for k in ["ID", "EN", "PL", "section", "kind", "metadata"]
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(args.output)
    restored = load_workbook(args.output)
    counts = {
        section: restored[section].max_row - 1
        for section in workbook.sheetnames
        if section not in {"Read first", "_baseline"}
    }
    ids = [row[0] for row in restored["_baseline"].iter_rows(min_row=2, values_only=True)]
    assert len(ids) == len(set(ids)) == len(rows)
    assert sum(counts.values()) == len(rows)
    summary = {
        "workbook": args.output.name,
        "rows": len(rows),
        "sheets": counts,
        "effective_exact_catalog_entries": len(exact),
        "catalog_entries_exported": len(english),
        "baseline_commit": baseline,
        "source_sha256": source_digest,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "provider_calls": 0,
        "private_runtime_data": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
