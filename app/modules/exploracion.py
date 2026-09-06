from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.shared.csv_utils import read_csv, records

router = APIRouter(tags=["1. Exploración"])


class ColumnInfo(BaseModel):
    nombre: str
    tipo: str
    nulos: int


class ExplorationResult(BaseModel):
    filas: int
    columnas: int
    filas_duplicadas: int
    variables: list[ColumnInfo]
    vista_previa: list[dict[str, Any]]


def explore(df: pd.DataFrame) -> dict:
    return {
        "filas": len(df), "columnas": len(df.columns),
        "filas_duplicadas": int(df.duplicated().sum()),
        "variables": [
            {"nombre": col, "tipo": str(df[col].dtype), "nulos": int(df[col].isna().sum())}
            for col in df.columns
        ],
        "vista_previa": records(df.head(5)),
    }


@router.post("/exploracion", response_model=ExplorationResult)
def explorar(archivo: Annotated[UploadFile, File(description="CSV UTF-8 con cabecera")]):
    """Inspecciona el archivo sin modificarlo; devuelve hasta cinco filas."""
    return explore(read_csv(archivo))
