from copy import deepcopy

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.datos import DATOS
from app.main import app
from app.modules.estadistica import summarize
from app.modules.limpieza import MissingStrategy, clean

client = TestClient(app)


def test_health_and_docs():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    schema = client.get("/openapi.json").json()
    for endpoint in ("exploracion", "limpieza", "estadistica"):
        operation = schema["paths"]["/api/" + endpoint]["get"]
        assert "requestBody" not in operation


def test_exploration():
    response = client.get("/api/exploracion")
    assert response.status_code == 200
    data = response.json()
    assert data["filas"] == 6
    assert data["columnas"] == 4
    assert data["filas_duplicadas"] == 1
    assert len(data["vista_previa"]) == 5
    assert sum(v["nulos"] for v in data["variables"]) == 2


def test_cleaning_and_statistics_workflow():
    params = {"estrategia": "mediana", "eliminar_duplicados": True}
    response = client.get("/api/limpieza", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["filas_resultado"] == 5
    assert data["nulos_restantes"] == 0
    assert len(data["datos"]) == 5
    stats = client.get("/api/estadistica", params={**params, "columnas": "venta_bs"}).json()
    values = stats["estadisticas"]["venta_bs"]
    assert values["media"] == pytest.approx(37.6)
    assert values["mediana"] == 38
    assert values["minimo"] == 24
    assert values["maximo"] == 50
    assert stats == summarize(pd.DataFrame(data["datos"]), "venta_bs")


@pytest.mark.parametrize("strategy,expected,nulls", [
    ("media", 5, 0), ("mediana", 5, 0), ("eliminar", 3, 0), ("conservar", 5, 2),
])
def test_strategies(strategy, expected, nulls):
    response = client.get("/api/limpieza", params={"estrategia": strategy})
    assert response.status_code == 200
    assert response.json()["filas_resultado"] == expected
    assert response.json()["nulos_restantes"] == nulls


def test_keep_duplicates():
    result = client.get("/api/limpieza", params={"eliminar_duplicados": False}).json()
    assert result["filas_resultado"] == 6
    assert result["datos"][3]["cantidad"] is None


def test_original_statistics():
    data = client.get("/api/estadistica").json()
    assert data["filas"] == 6
    assert data["estadisticas"]["venta_bs"]["media"] == 40
    stats = summarize(pd.DataFrame([{"x": 1}, {"x": 3}]), None)["estadisticas"]["x"]
    assert stats["mediana"] == 2
    assert stats["desviacion_estandar_muestral"] == pytest.approx(2 ** .5)


def test_null_and_single_value():
    data = summarize(pd.DataFrame({"x": [5], "empty": [float("nan")]}), None)["estadisticas"]
    assert data["x"]["desviacion_estandar_muestral"] is None
    assert data["empty"]["media"] is None


def test_text_nulls_remain():
    df = pd.DataFrame([{"x": 1, "label": "a", "empty": None},
                       {"x": 3, "label": None, "empty": None}])
    assert int(clean(df, MissingStrategy.media, True).isna().sum().sum()) == 3


@pytest.mark.parametrize("endpoint,params", [
    ("limpieza", {"estrategia": "inventada"}),
    ("limpieza", {"eliminar_duplicados": "invalido"}),
    ("estadistica", {"columnas": "inexistente"}),
    ("estadistica", {"columnas": "producto"}),
    ("estadistica", {"estrategia": "inventada"}),
])
def test_bad_parameters(endpoint, params):
    assert client.get("/api/" + endpoint, params=params).status_code == 422


def test_cleaning_without_remaining_rows():
    with pytest.raises(HTTPException) as error:
        clean(pd.DataFrame([{"x": None}]), MissingStrategy.eliminar, True)
    assert error.value.status_code == 422


def test_requests_do_not_modify_source():
    original = deepcopy(DATOS)
    before = client.get("/api/exploracion").json()
    client.get("/api/limpieza", params={"estrategia": "eliminar"})
    client.get("/api/estadistica", params={"estrategia": "media", "eliminar_duplicados": True})
    assert DATOS == original
    assert client.get("/api/exploracion").json() == before
