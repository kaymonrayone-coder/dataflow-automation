"""Command-line entry point."""
import argparse
import json
import sys
from .io import DataflowError
from .pipeline import run_pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Clean, validate and consolidate CSV/XLSX files")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--required", nargs="+", default=[])
    parser.add_argument("--numeric", nargs="+", default=[])
    parser.add_argument("--dedupe-on", nargs="+")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--sheet", default=0, help="Excel sheet name; default: first sheet")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = run_pipeline(args.inputs, args.output, required=args.required, numeric=args.numeric,
                              dedupe_on=args.dedupe_on, delimiter=args.delimiter,
                              sheet=args.sheet, overwrite=args.overwrite)
    except (DataflowError, OSError) as exc:
        print(f"dataflow: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
