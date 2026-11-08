"""Consolidation orchestration and execution report."""
import json
from pathlib import Path
import pandas as pd
from .cleaning import clean
from .io import DataflowError, read_table, write_table
from .validation import validate


def run_pipeline(inputs, output, *, required=None, numeric=None, dedupe_on=None,
                 delimiter=",", sheet=0, overwrite=False):
    paths = [Path(p).resolve() for p in inputs]
    output = Path(output).resolve()
    rejected_path = output.with_name(output.stem + ".rejected.csv")
    report_path = output.with_name(output.stem + ".report.json")
    targets = [output, rejected_path, report_path]
    if not paths or len(set(paths)) != len(paths):
        raise DataflowError("Provide at least one input, without repeated paths")
    if output.suffix.lower() not in (".csv", ".xlsx"):
        raise DataflowError("Output must be .csv or .xlsx")
    if set(paths) & set(targets):
        raise DataflowError("Output artifacts cannot overwrite inputs")
    if not overwrite and any(p.exists() for p in targets):
        raise DataflowError("Output artifacts already exist; use --overwrite explicitly")
    frames = []
    counts = []
    for path in paths:
        raw = read_table(path, delimiter=delimiter, sheet=sheet)
        frame = clean(raw)
        counts.append({"file": path.name, "rows_read": len(raw), "blank_rows_removed": len(raw)-len(frame)})
        # Validate per file: required schema must not be concealed by union concatenation.
        validate(frame, required or [], numeric or [])
        frame["df_source"] = path.name
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    valid, rejected = validate(combined, required or [], numeric or [])
    columns = dedupe_on if dedupe_on else [c for c in valid.columns if c != "df_source"]
    missing = set(columns) - set(valid.columns)
    if missing:
        raise DataflowError(f"Unknown deduplication columns: {', '.join(sorted(missing))}")
    result = valid.drop_duplicates(subset=columns, keep="first")
    report = {"files": counts, "rows_read": sum(c["rows_read"] for c in counts),
              "blank_rows_removed": sum(c["blank_rows_removed"] for c in counts),
              "invalid_rows": len(rejected), "duplicates_removed": len(valid)-len(result),
              "rows_written": len(result), "dedupe_columns": columns}
    output.parent.mkdir(parents=True, exist_ok=True)
    write_table(result, output)
    write_table(rejected, rejected_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return report
