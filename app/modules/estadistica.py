from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.shared.csv_utils import finite, read_csv

router = APIRouter(tags=["3. Estadística"])


class ColumnStats(BaseModel):
    cantidad_validos: int
    nulos: int
    media: float | None
    mediana: float | None
    minimo: float | None
    maximo: float | None
    desviacion_estandar_muestral: float | None


class StatisticsResult(BaseModel):
    filas: int
    estadisticas: dict[str, ColumnStats]


def summarize(df: pd.DataFrame, columns: str | None) -> dict:
    selected = df.select_dtypes(include="number")
    if columns:
        names = list(dict.fromkeys(name.strip() for name in columns.split(",")))
        if any(name not in df.columns for name in names):
            raise HTTPException(422, "Alguna columna solicitada no existe.")
        if any(name not in selected.columns for name in names):
            raise HTTPException(422, "Selecciona únicamente columnas numéricas.")
        selected = selected[names]
    if selected.shape[1] == 0:
        raise HTTPException(422, "El archivo no contiene columnas numéricas.")
    stats = {}
    for col in selected.columns:
        series = selected[col]
        valid = series.dropna()
        stats[col] = {
            "cantidad_validos": int(valid.count()), "nulos": int(series.isna().sum()),
            "media": finite(valid.mean()) if len(valid) else None,
            "mediana": finite(valid.median()) if len(valid) else None,
            "minimo": finite(valid.min()) if len(valid) else None,
            "maximo": finite(valid.max()) if len(valid) else None,
            "desviacion_estandar_muestral": finite(valid.std(ddof=1)) if len(valid) > 1 else None,
        }
    return {"filas": len(df), "estadisticas": stats}


@router.post("/estadistica", response_model=StatisticsResult)
def estadistica(
    archivo: Annotated[UploadFile, File()],
    columnas: Annotated[str | None, Form(description="Opcional: nombres separados por comas")] = None,
):
    """Ignora nulos por columna. Desviación muestral (n−1), null si n < 2."""
    return summarize(read_csv(archivo), columnas)
