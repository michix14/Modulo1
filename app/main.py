from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.modules import exploracion, limpieza, estadistica

app = FastAPI(
    title="DataScience API", version="1.0.0",
    description="Tres módulos: exploración, limpieza y estadística. CSV UTF-8, "
    "separado por comas, hasta 1 MB, 10.000 filas y 50 columnas. "
    "Cada petición es independiente; no se conservan los archivos.",
)
for module in (exploracion, limpieza, estadistica):
    app.include_router(module.router, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
