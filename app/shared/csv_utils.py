import csv
import io
import json

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile

MAX_BYTES = 1_000_000
MAX_ROWS = 10_000
MAX_COLUMNS = 50


def read_csv(file: UploadFile) -> pd.DataFrame:
    """Valida estructura antes de inferir tipos. Nunca escribe el dataset a disco."""
    try:
        if not (file.filename or "").lower().endswith(".csv"):
            raise HTTPException(415, "El archivo debe tener extensión .csv.")
        content = file.file.read(MAX_BYTES + 1)
    finally:
        file.file.close()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "El CSV supera el límite de 1 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Guarda el CSV con codificación UTF-8.")
    if not text.strip() or "\x00" in text:
        raise HTTPException(400, "Archivo vacío o contenido no válido.")
    try:
        rows = csv.reader(io.StringIO(text), strict=True)
        header = next(rows)
        if not header or any(not name.strip() for name in header):
            raise HTTPException(400, "Todas las columnas deben tener nombre.")
        if len(set(header)) != len(header):
            raise HTTPException(400, "Hay nombres de columnas duplicados.")
        if len(header) > MAX_COLUMNS:
            raise HTTPException(413, "Máximo 50 columnas.")
        count = 0
        for row in rows:
            if not row:
                continue
            if len(row) != len(header):
                raise HTTPException(400, "Las filas deben tener tantas celdas como la cabecera.")
            count += 1
            if count > MAX_ROWS:
                raise HTTPException(413, "Máximo 10.000 filas.")
        if not count:
            raise HTTPException(400, "El CSV no contiene filas de datos.")
        df = pd.read_csv(io.StringIO(text))
    except (csv.Error, StopIteration, pd.errors.ParserError, pd.errors.EmptyDataError):
        raise HTTPException(400, "CSV mal formado; usa comas como separador.")
    numeric = df.select_dtypes(include="number")
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise HTTPException(400, "No se admiten valores numéricos infinitos.")
    return df


def records(df: pd.DataFrame) -> list[dict]:
    """Pandas convierte NaN en null para producir JSON válido."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


def finite(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None
