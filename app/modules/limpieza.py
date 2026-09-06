from enum import Enum
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.shared.csv_utils import read_csv

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


@router.post("/limpieza", response_class=Response,
             responses={200: {"content": {"text/csv": {}}, "description": "CSV limpio descargable"}})
def limpiar(
    archivo: Annotated[UploadFile, File()],
    estrategia: Annotated[MissingStrategy, Form()] = MissingStrategy.conservar,
    eliminar_duplicados: Annotated[bool, Form()] = True,
):
    """Media/mediana solo rellenan columnas numéricas con datos disponibles.

    Los nulos de texto y de columnas totalmente vacías permanecen.
    No se vuelve a deduplicar después de imputar valores.
    """
    original = read_csv(archivo)
    result = clean(original, estrategia, eliminar_duplicados)
    return Response(
        result.to_csv(index=False).encode("utf-8-sig"), media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="datos_limpios.csv"',
            "X-Filas-Originales": str(len(original)),
            "X-Filas-Resultado": str(len(result)),
            "X-Nulos-Restantes": str(int(result.isna().sum().sum())),
        },
    )
