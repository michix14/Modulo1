# DataScience API

Proyecto académico con Python, FastAPI y Pandas para explorar, limpiar y analizar datos. Los datos están en una **lista de diccionarios** en `app/datos.py`; no se cargan ni se generan archivos CSV.

## Ejecutar

Requiere Python 3.12. Desde la carpeta del proyecto, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abre http://127.0.0.1:8000/docs. Selecciona una operación, pulsa **Try it out** y luego **Execute**. No necesitas subir archivos ni enviar un cuerpo de petición.

## Modificar los datos

Edita `DATOS` en `app/datos.py`. Cada diccionario representa una venta y sus claves son las columnas:

```python
DATOS = [
    {"producto": "Pan integral", "cantidad": 10, "precio_unitario": 5, "venta_bs": 50},
    {"producto": "Empanada", "cantidad": None, "precio_unitario": 6, "venta_bs": 36},
]
```

Usa las mismas claves en cada registro, números sin comillas y `None` para los valores faltantes. Mantén al menos una fila. El servidor con `--reload` carga los cambios al guardar el archivo.

Cada petición crea una tabla de Pandas a partir de la lista. La limpieza no modifica la lista original ni guarda cambios entre peticiones. Todas las respuestas son JSON; `None` aparece como `null`.

## Operaciones

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/health` | Estado de la API |
| GET | `/api/exploracion` | Filas, columnas, tipos, nulos, duplicados y cinco filas de vista previa |
| GET | `/api/limpieza` | Lista limpia y conteos de filas y nulos |
| GET | `/api/estadistica` | Media, mediana, mínimo, máximo y desviación estándar muestral |

`limpieza` y `estadistica` aceptan estos parámetros en la URL:

| Parámetro | Opciones |
| --- | --- |
| `estrategia` | `conservar` (predeterminada), `eliminar`, `media`, `mediana` |
| `eliminar_duplicados` | `true` o `false`; predeterminado `true` en limpieza y `false` en estadística |

Estadística también acepta `columnas`, con nombres separados por comas. Si se omite, analiza todas las columnas numéricas. Por defecto calcula sobre los datos originales; para analizar datos limpios, indica las mismas opciones que en limpieza.

Primero se quitan duplicados y después se tratan los nulos. Media y mediana rellenan solo columnas numéricas con valores disponibles. Los nulos de texto y las columnas completamente vacías permanecen. No se vuelven a quitar duplicados después de rellenar. Si se eliminan todas las filas, se devuelve un error 422.

Las estadísticas ignoran los nulos. La desviación estándar usa el divisor `n - 1` y devuelve `null` con menos de dos valores. Los parámetros inválidos y las columnas inexistentes o no numéricas producen un error 422.

## Demostración

Abre estas direcciones en el navegador con el servidor en marcha:

1. http://127.0.0.1:8000/api/exploracion — muestra 6 filas, 4 columnas, 1 duplicado y 2 nulos.
2. http://127.0.0.1:8000/api/limpieza?estrategia=mediana — devuelve 5 registros sin nulos, en el campo `datos`.
3. http://127.0.0.1:8000/api/estadistica?columnas=venta_bs — la media original es 40 Bs.
4. http://127.0.0.1:8000/api/estadistica?columnas=venta_bs&estrategia=mediana&eliminar_duplicados=true — la media después de limpiar es 37,6 Bs.

## Estructura

- `app/datos.py`: lista de ventas que puedes editar.
- `app/main.py`: aplicación y registro de rutas.
- `app/modules/exploracion.py`: diagnóstico de los datos.
- `app/modules/limpieza.py`: tratamiento de duplicados y nulos.
- `app/modules/estadistica.py`: cálculos descriptivos.
- `app/shared/data_utils.py`: conversión entre lista, tabla y JSON.
- `tests/test_api.py`: pruebas de los endpoints y los cálculos.

Se mantienen los tres módulos funcionales. Pandas realiza el procesamiento tabular y FastAPI publica las operaciones y su documentación interactiva.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas comprueban los resultados conocidos, las estrategias de limpieza, los errores y que la lista original no cambie. No necesitan internet.

Esta versión cambia los anteriores endpoints POST con archivos por endpoints GET con datos locales. Los clientes anteriores deben actualizarse a las rutas y parámetros descritos aquí.
