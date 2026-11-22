"""Validate an edited EN/PL workbook and optionally write its changes; never modify the app.

Requires optional openpyxl tooling. IDs/placeholders/error codes and hidden originals must survive
editing. The initial unedited workbook and an ordinary EN/PL correction can use the same command.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def protected(value):
    return Counter(re.findall(r"\{[A-Za-z0-9_]+\}|\b(?:GUI|SPEECH|USER)_[A-Z0-9_]+\b", value))


def inspect(path):
    from openpyxl import load_workbook

    book = load_workbook(path, data_only=False)
    originals = {}
    for row in book["_baseline"].iter_rows(min_row=2, values_only=True):
        identifier, en, pl, section, kind, metadata = row
        assert identifier not in originals, f"Duplicate baseline ID: {identifier}"
        originals[identifier] = dict(
            EN=en or "", PL=pl or "", section=section, kind=kind, metadata=json.loads(metadata)
        )
    changes, seen = [], set()
    for section in {record["section"] for record in originals.values()}:
        sheet = book[section]
        assert [c.value for c in sheet[1]] == ["ID", "EN", "PL", "Context", "Review", "Notes"]
        for cells in sheet.iter_rows(min_row=2):
            identifier, en, pl, _, _, notes = [cell.value for cell in cells]
            assert identifier in originals and identifier not in seen, (
                f"Unknown/duplicate ID: {identifier}"
            )
            seen.add(identifier)
            original = originals[identifier]
            assert original["section"] == section, f"Moved row: {identifier}"
            current = {"EN": en, "PL": pl}
            for language, value in current.items():
                assert isinstance(value, str) and value.strip(), f"Empty {language}: {identifier}"
                assert cells[1 if language == "EN" else 2].data_type != "f", (
                    f"Formula: {identifier}"
                )
                assert protected(value) == protected(original[language]), (
                    f"Changed placeholders/codes in {language}: {identifier}"
                )
            if en != original["EN"] or pl != original["PL"] or notes:
                changes.append(
                    dict(ID=identifier, EN=en, PL=pl, Notes=notes or "", original=original)
                )
    assert seen == set(originals), f"Removed rows: {set(originals) - seen}"
    return {"rows": len(seen), "changes": changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--diff-output", type=Path)
    args = parser.parse_args()
    result = inspect(args.workbook)
    if args.diff_output:
        args.diff_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "rows": result["rows"],
                "changed_rows": len(result["changes"]),
                "valid": True,
                "application_modified": False,
            }
        )
    )


if __name__ == "__main__":
    main()
