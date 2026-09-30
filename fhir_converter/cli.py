"""Command-line interface.

    python -m fhir_converter samples/demo_patient.json
    python -m fhir_converter samples/batch.json --bundle -o out.json

Exit codes: 0 = all records converted, 1 = some records invalid, 2 = unreadable input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import convert_many, load_records


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fhir_converter", description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path, help="JSON file with one form object or an array")
    ap.add_argument("-o", "--output", type=Path, help="write FHIR JSON here instead of stdout")
    ap.add_argument("--bundle", action="store_true", help="wrap patients in a collection Bundle")
    args = ap.parse_args(argv)

    try:
        records = load_records(args.input)
    except (OSError, ValueError) as exc:  # json.JSONDecodeError is a ValueError
        print(f"{args.input}: cannot read input: {exc}", file=sys.stderr)
        return 2

    results = convert_many(records)
    for r in results:
        for e in r.errors:
            print(f"record {r.index}: {e.field}: {e.message}", file=sys.stderr)

    patients = [r.patient for r in results if r.ok]
    if args.bundle:
        output: object = {"resourceType": "Bundle", "type": "collection",
                          "entry": [{"fullUrl": f"urn:uuid:{p['id']}", "resource": p}
                                    for p in patients]}
    else:
        output = patients[0] if len(records) == 1 and patients else patients

    text = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
