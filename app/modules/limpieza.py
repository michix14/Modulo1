from enum import Enum

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.shared.data_utils import dataframe, records

router = APIRouter(tags=["2. Limpieza"])


class MissingStrategy(str, Enum):
    conservar = "conservar"
    eliminar = "eliminar"
    media = "media"
    mediana = "mediana"


def clean(df: pd.DataFrame, strategy: MissingStrategy, duplicates: bool) -> pd.DataFrame:
    """Copia, quita duplicados y trata nulos en ese orden."""
    result = df.copy()
    if duplicates:
        result = result.drop_duplicates()
    if strategy == MissingStrategy.eliminar:
        result = result.dropna()
    elif strategy in (MissingStrategy.media, MissingStrategy.mediana):
        for col in result.select_dtypes(include="number").columns:
            # Una columna completamente vacía no tiene media ni mediana.
            if result[col].notna().any():
                value = (result[col].mean() if strategy == MissingStrategy.media
                         else result[col].median())
                result[col] = result[col].fillna(value)
    if result.empty:
        raise HTTPException(422, "La limpieza eliminaría todas las filas.")
    return result


@router.get("/limpieza")
def limpiar(
    estrategia: MissingStrategy = MissingStrategy.conservar,
    eliminar_duplicados: bool = True,
):
    """Media/mediana solo rellenan columnas numéricas con datos disponibles.

    Los nulos de texto y de columnas totalmente vacías permanecen.
    No se vuelve a deduplicar después de imputar valores.
    """
    original = dataframe()
    result = clean(original, estrategia, eliminar_duplicados)
    return {
        "filas_originales": len(original),
        "filas_resultado": len(result),
        "nulos_restantes": int(result.isna().sum().sum()),
        "datos": records(result),
    }
