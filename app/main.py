from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.modules import exploracion, limpieza, estadistica

app = FastAPI(
    title="DataScience API", version="1.0.0",
    description="Exploración, limpieza y estadística de una lista de ventas "
    "definida en app/datos.py. Cada petición trabaja con una copia de los datos.",
)
for module in (exploracion, limpieza, estadistica):
    app.include_router(module.router, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
