import json
import math

import pandas as pd

from app.datos import DATOS


def dataframe() -> pd.DataFrame:
    """Crea una tabla nueva para no modificar la lista original."""
    return pd.DataFrame(DATOS)


def records(df: pd.DataFrame) -> list[dict]:
    """Convierte la tabla en una lista con null en los valores faltantes."""
    return json.loads(df.to_json(orient="records"))


def finite(value):
    return float(value) if pd.notna(value) and math.isfinite(value) else None
