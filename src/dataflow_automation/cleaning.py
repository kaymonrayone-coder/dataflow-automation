"""Deterministic normalization without guessing data types."""
import re
import unicodedata
import pandas as pd
from .io import DataflowError


def normalize_header(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip()).strip("_")


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    headers = [normalize_header(col) for col in result.columns]
    if any(not col for col in headers) or len(set(headers)) != len(headers):
        raise DataflowError("Empty or colliding normalized column names")
    if any(col.startswith("_df_") or col.startswith("df_") for col in headers):
        raise DataflowError("Column prefix df_ is reserved for provenance and errors")
    result.columns = headers
    for col in headers:
        result[col] = result[col].astype("string").str.strip().replace("", pd.NA)
    return result.dropna(how="all").reset_index(drop=True)
