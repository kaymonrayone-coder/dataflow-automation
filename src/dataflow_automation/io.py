"""Text-preserving import and safe spreadsheet export."""
from pathlib import Path
from zipfile import BadZipFile
import pandas as pd


class DataflowError(ValueError):
    """An actionable input or configuration error."""


def read_table(path: Path, *, delimiter: str = ",", sheet: str | int = 0) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, dtype="string", sep=delimiter, keep_default_na=False)
        if path.suffix.lower() == ".xlsx":
            return pd.read_excel(path, dtype="string", sheet_name=sheet, keep_default_na=False)
        raise DataflowError(f"Unsupported input format: {path}")
    except (OSError, ValueError, UnicodeError, ImportError, BadZipFile) as exc:
        raise DataflowError(f"Cannot read {path}: {exc}") from exc


def write_table(frame: pd.DataFrame, path: Path) -> None:
    # Neutralize formulas when exported files are opened in spreadsheet software.
    safe = frame.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(lambda v: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v)
    if path.suffix.lower() == ".csv":
        safe.to_csv(path, index=False)
    elif path.suffix.lower() == ".xlsx":
        safe.to_excel(path, index=False, engine="openpyxl")
    else:
        raise DataflowError("Output must be .csv or .xlsx")
