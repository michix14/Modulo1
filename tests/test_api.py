from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "ventas.csv"


def post(endpoint, content=b"x,y\n1,2\n3,4\n", data=None, filename="datos.csv"):
    return client.post("/api/" + endpoint,
                       files={"archivo": (filename, content, "text/csv")}, data=data or {})


def test_health_and_docs():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_exploration():
    data = post("exploracion", EXAMPLE.read_bytes()).json()
    assert data["filas"] == 6
    assert data["columnas"] == 4
    assert data["filas_duplicadas"] == 1
    assert sum(v["nulos"] for v in data["variables"]) == 2


def test_cleaning_and_statistics_workflow():
    response = post("limpieza", EXAMPLE.read_bytes(), {"estrategia": "mediana"})
    assert response.status_code == 200
    assert response.headers["x-filas-resultado"] == "5"
    assert response.headers["x-nulos-restantes"] == "0"
    stats = post("estadistica", response.content, {"columnas": "venta_bs"}).json()
    assert stats["estadisticas"]["venta_bs"]["media"] == pytest.approx(37.6)


@pytest.mark.parametrize("strategy,expected", [("media", 5), ("mediana", 5), ("eliminar", 3), ("conservar", 5)])
def test_strategies(strategy, expected):
    result = post("limpieza", EXAMPLE.read_bytes(), {"estrategia": strategy})
    assert result.status_code == 200
    assert int(result.headers["x-filas-resultado"]) == expected


def test_keep_duplicates():
    assert post("limpieza", EXAMPLE.read_bytes(), {"eliminar_duplicados": "false"}).headers["x-filas-resultado"] == "6"


def test_statistics():
    stats = post("estadistica").json()["estadisticas"]["x"]
    assert stats["media"] == 2
    assert stats["mediana"] == 2
    assert stats["desviacion_estandar_muestral"] == pytest.approx(2 ** .5)


def test_null_and_single_value():
    data = post("estadistica", b"x,empty\n5,\n").json()["estadisticas"]
    assert data["x"]["desviacion_estandar_muestral"] is None
    assert data["empty"]["media"] is None


def test_text_nulls_remain():
    response = post("limpieza", b"x,label,empty\n1,a,\n3,,\n", {"estrategia": "media"})
    assert response.status_code == 200
    assert response.headers["x-nulos-restantes"] == "3"


@pytest.mark.parametrize("content", [b"", b"x,y\n", b"x,x\n1,2\n", b"x,\n1,2\n", b"x,y\n1,2,3\n", b'x,y\n"unclosed,2', b"x\n\xff", b"x\ninf\n", b"x\n\x00\n"])
def test_invalid_csv(content):
    assert post("exploracion", content).status_code == 400


def test_upload_limits():
    assert post("exploracion", b"x" * 1_000_001).status_code == 413
    assert post("exploracion", b"x\n" + b"1\n" * 10_001).status_code == 413
    content = (",".join("c" + str(i) for i in range(51)) + "\n" + ",".join(["1"] * 51)).encode()
    assert post("exploracion", content).status_code == 413


def test_bad_parameters():
    assert post("exploracion", filename="datos.txt").status_code == 415
    assert post("limpieza", data={"estrategia": "inventada"}).status_code == 422
    assert post("estadistica", data={"columnas": "inexistente"}).status_code == 422
    assert post("estadistica", b"label\na\nb\n").status_code == 422
    assert post("estadistica", b"x,label\n1,a\n", {"columnas": "label"}).status_code == 422
    assert post("limpieza", b"x,y\n1,\n", {"estrategia": "eliminar"}).status_code == 422
    assert client.post("/api/exploracion").status_code == 422


def test_bom_and_quoted_comma():
    assert post("exploracion", '\ufeffx,label\n1,"a,b"\n'.encode()).status_code == 200


def test_uploaded_data_not_reused():
    post("exploracion", b"first\n1\n")
    assert post("exploracion", b"second\n2\n").json()["variables"][0]["nombre"] == "second"
