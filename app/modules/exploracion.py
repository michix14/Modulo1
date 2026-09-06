from typing import Any

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from app.shared.data_utils import dataframe, records

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


@router.get("/exploracion", response_model=ExplorationResult)
def explorar():
    """Inspecciona la lista de ventas y devuelve hasta cinco filas."""
    return explore(dataframe())
