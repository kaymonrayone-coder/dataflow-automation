"""Explicit required-field and numeric validation."""
import pandas as pd
from .io import DataflowError


def validate(frame: pd.DataFrame, required: list[str], numeric: list[str]):
    missing = set(required + numeric) - set(frame.columns)
    if missing:
        raise DataflowError(f"Missing configured columns: {', '.join(sorted(missing))}")
    reasons = pd.Series("", index=frame.index, dtype="string")
    for col in required:
        mask = frame[col].isna()
        reasons.loc[mask] += f"required:{col};"
    for col in numeric:
        values = pd.to_numeric(frame[col], errors="coerce")
        mask = frame[col].notna() & (values.isna() | values.isin([float("inf"), float("-inf")]))
        reasons.loc[mask] += f"numeric:{col};"
    rejected = frame.loc[reasons.ne("")].copy()
    rejected["df_errors"] = reasons.loc[reasons.ne("")]
    return frame.loc[reasons.eq("")].copy(), rejected
