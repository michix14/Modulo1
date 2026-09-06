# DataScience API · Python + FastAPI + Vercel

Proyecto académico para una maestría en Ciencias de Datos: explorar, limpiar y analizar conjuntos de datos tabulares. Los tres módulos funcionales son `exploracion.py`, `limpieza.py` y `estadistica.py`. Cada uno incluye un router HTTP y una función de procesamiento separada. `shared/` contiene utilidades, no un cuarto módulo funcional.

## 1. Requisitos

- Python 3.12 (versión indicada en `.python-version`).
- Git y una cuenta de Vercel para desplegar desde un repositorio.
- Archivos CSV UTF-8, con cabecera, separados por comas y punto decimal.

No se necesitan base de datos, claves API, Docker, frontend, ni variables de entorno. No hay persistencia entre solicitudes. El alcance es una demostración académica, no una plataforma de procesamiento masivo.

## 2. Instalación en Windows

Descomprime el ZIP y abre una terminal dentro de `datascience_api`, donde está este README:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Los comandos utilizan directamente el Python del entorno virtual: no necesitas cambiar la política de ejecución de PowerShell ni activar scripts.

En Linux/macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

Abre [Swagger local](http://127.0.0.1:8000/docs). La raíz `/` redirige a `/docs`; `/health` devuelve `{"status":"ok"}`. Para instalar sin pruebas usa `requirements.txt`.

## 3. Estructura

| Archivo o carpeta | Responsabilidad |
| --- | --- |
| `app/main.py` | Crea FastAPI y registra los tres routers |
| `app/modules/exploracion.py` | Estructura, duplicados, nulos y vista previa |
| `app/modules/limpieza.py` | Tratamiento de nulos y descarga del resultado |
| `app/modules/estadistica.py` | Estadística descriptiva numérica |
| `app/shared/csv_utils.py` | Lectura y validación común del CSV |
| `examples/ventas.csv` | Datos ficticios para la demostración |
| `tests/test_api.py` | Pruebas HTTP y flujo completo |
| `.python-version` | Python 3.12 para despliegue |
| `.vercelignore` | Evita incluir archivos de desarrollo en el despliegue |

## 4. Demostración paso a paso en Swagger

### A. Explorar

1. Abre `POST /api/exploracion` y pulsa **Try it out**.
2. En `archivo`, selecciona `examples/ventas.csv`.
3. Pulsa **Execute**.
4. Obtendrás 6 filas, 4 columnas, 1 fila duplicada y 2 valores nulos. La vista previa incluye como máximo 5 filas.

Los tipos corresponden a la inferencia de Pandas; una columna numérica con nulos puede aparecer como `float64`. Los identificadores con ceros iniciales no se preservan necesariamente como texto: esta versión no permite definir un esquema de tipos.

### B. Limpiar

1. Abre `POST /api/limpieza` → **Try it out**.
2. Sube el mismo CSV.
3. Elige `estrategia=mediana` y `eliminar_duplicados=true`.
4. Ejecuta y descarga la respuesta como `datos_limpios.csv`.
5. El resultado tendrá 5 filas y ningún nulo en este ejemplo.

| Estrategia | Comportamiento |
| --- | --- |
| `conservar` | No cambia los nulos |
| `eliminar` | Elimina filas con al menos un nulo |
| `media` | Completa nulos numéricos con la media de su columna |
| `mediana` | Completa nulos numéricos con la mediana de su columna |

Primero se eliminan duplicados de fila completa, luego se tratan los nulos. La media y la mediana se calculan después de deduplicar. Los nulos de texto y columnas totalmente vacías permanecen al imputar; no se inventan valores. No se deduplica de nuevo después de imputar. Si la operación elimina todas las filas, devuelve 422. El CSV original nunca se modifica.

Las cabeceras `X-Filas-Originales`, `X-Filas-Resultado` y `X-Nulos-Restantes` muestran el efecto de la limpieza.

### C. Calcular estadísticas

1. Abre `POST /api/estadistica` → **Try it out**.
2. Sube `datos_limpios.csv`.
3. En `columnas`, escribe `venta_bs`; si lo dejas vacío se analizan todas las columnas numéricas.
4. Ejecuta: la media de `venta_bs` será **37,6 Bs**, mediana **38 Bs**, mínimo **24 Bs** y máximo **50 Bs**.

Sin limpieza, la media de `venta_bs` es 40 Bs: tiene un duplicado y se omite un nulo. La comparación permite explicar cómo la preparación modifica los resultados; imputar no equivale a recuperar el valor real perdido.

Cada endpoint recibe su propio archivo: la API no conserva el CSV de la petición anterior ni utiliza `dataset_id`.

## 5. Endpoints y ejemplos curl

| Método | Ruta | Entrada | Salida |
| --- | --- | --- | --- |
| GET | `/health` | Ninguna | Estado JSON |
| POST | `/api/exploracion` | `archivo` | Resumen JSON |
| POST | `/api/limpieza` | `archivo`, `estrategia`, `eliminar_duplicados` | CSV descargable |
| POST | `/api/estadistica` | `archivo`, `columnas` opcional | Indicadores JSON |

Las entradas POST son `multipart/form-data`, no JSON. En PowerShell usa `curl.exe` en lugar de `curl` si existe el alias antiguo.

```bash
curl -X POST http://127.0.0.1:8000/api/exploracion -F "archivo=@examples/ventas.csv"
curl -X POST http://127.0.0.1:8000/api/limpieza -F "archivo=@examples/ventas.csv" -F "estrategia=mediana" -F "eliminar_duplicados=true" -o datos_limpios.csv
curl -X POST http://127.0.0.1:8000/api/estadistica -F "archivo=@datos_limpios.csv" -F "columnas=cantidad,venta_bs"
```

## 6. Desplegar en Vercel

1. Crea un repositorio en GitHub o GitLab y sube el contenido de `datascience_api`. No subas el ZIP, `.venv`, cachés ni datos privados. Incluye `.python-version`.
2. En Vercel, crea un proyecto e importa ese repositorio.
3. Establece **Root Directory** en la carpeta que contiene `requirements.txt`. Si subiste los archivos a la raíz del repositorio, deja la raíz; si subiste la carpeta contenedora, elige `datascience_api`.
4. Comprueba la detección de FastAPI. Mantén la configuración predeterminada; este proyecto no necesita Build Command, Output Directory ni un comando de arranque Uvicorn en Vercel.
5. Despliega y revisa los logs. Vercel detecta la instancia `app` de `app/main.py` y las dependencias de `requirements.txt`.
6. Abre `https://TU-PROYECTO.vercel.app/health` y después `/docs`.
7. Repite la demostración de los tres módulos. Revisa la protección de despliegue y comparte el acceso solo con quien corresponda; prueba el enlace con el acceso que tendrá tu docente.

No se incluye un `vercel.json` con reglas antiguas `builds/routes`: el punto de entrada está soportado de forma nativa. `.python-version` fija el intérprete, y las dependencias directas están fijadas a versiones probadas; las transitivas no están bloqueadas.

Alternativa con Vercel CLI instalada, desde la raíz del proyecto:

```bash
vercel
vercel --prod
```

El segundo comando publica en producción; ejecútalo solo cuando hayas validado el proyecto. La entrega del ZIP no publica nada en tu cuenta.

Fuentes oficiales de despliegue, consultadas el 6 de septiembre de 2026:

- [FastAPI en Vercel: detección y despliegue](https://vercel.com/docs/frameworks/backend/fastapi)
- [Runtime Python](https://vercel.com/docs/functions/runtimes/python)
- [Sistema de archivos y ejecución de funciones](https://vercel.com/docs/functions/runtimes)

## 7. Límites, errores y seguridad

- CSV hasta 1.000.000 bytes, 10.000 filas de datos y 50 columnas. Las líneas vacías se omiten. La cabecera debe tener nombres únicos, no vacíos, y todas las filas el mismo número de celdas.
- Se admite BOM UTF-8. No se admiten Excel, ZIP, otros delimitadores ni valores numéricos infinitos. Pandas reconoce celdas vacías y sus marcadores habituales (por ejemplo `NA`) como valores faltantes.
- 400: CSV vacío, inválido, sin filas o codificación incorrecta. 413: límite excedido. 415: extensión distinta de `.csv`. 422: parámetros incorrectos, columnas no numéricas/inexistentes, archivo faltante o limpieza sin filas restantes.
- Las medias ignoran nulos por columna. Desviación estándar muestral: divisor `n−1`. Con menos de dos observaciones devuelve `null`; una columna vacía devuelve indicadores `null`, no cero.
- Los límites de la plataforma se aplican además de los propios. La lectura limitada del archivo ocurre después del procesamiento multipart de FastAPI; no sustituye los controles de tamaño y abuso de la plataforma.
- La aplicación no guarda datasets ni registra sus contenidos. FastAPI puede usar almacenamiento temporal durante el procesamiento de una subida; no se utiliza como persistencia. Los endpoints son síncronos para ejecutar Pandas fuera del bucle asíncrono principal.
- No hay autenticación, cuotas ni limitación de peticiones propia. Usa únicamente datos ficticios para la tarea. Una aplicación pública requiere controles adicionales y seguimiento de consumo.
- El CSV conserva textos originales. Si provienen de desconocidos, no abras directamente el resultado en Excel: podría contener fórmulas de hoja de cálculo. La API no ejecuta esas fórmulas ni neutraliza su contenido para no cambiar los datos.
- No están incluidos entrenamiento de modelos, normalización, correlaciones ni procesamiento masivo: el alcance acordado es exploración, limpieza y estadística descriptiva.

## 8. Pruebas

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Linux/macOS:

```bash
.venv/bin/python -m pytest -q
```

Comprueban el flujo completo, fórmulas conocidas, estrategias de limpieza, nulos, duplicados, límites, codificación, selección de columnas y respuestas de error. No requieren internet ni una cuenta de Vercel. Swagger carga sus recursos de interfaz desde una CDN y requiere conexión para visualizarse normalmente.

Verificación de esta entrega: **24 pruebas aprobadas** en Python 3.12. Aparecieron dos advertencias de deprecación en dependencias del cliente de pruebas (Starlette/httpx y AnyIO), sin fallos. No se ha realizado un despliegue real en Vercel; la configuración se contrastó con su documentación oficial.

## 9. Explicación para la defensa

El problema es que los datos originales pueden tener valores faltantes y registros repetidos que alteran un análisis. El primer módulo permite diagnosticar esos problemas; el segundo aplica una política explícita de limpieza; el tercero obtiene medidas descriptivas sobre el resultado.

FastAPI publica las operaciones mediante HTTP y genera documentación interactiva. Pydantic valida parámetros y estructura las respuestas; Pandas procesa las tablas. Cada módulo tiene una responsabilidad clara y reutiliza la lectura validada del CSV. No son tres microservicios: son tres módulos de una misma aplicación.

La API es sin estado: cada solicitud contiene los datos necesarios y no depende de una instancia anterior. Esta decisión facilita ejecutarla en Vercel. La demostración permite discutir por qué eliminar filas o imputar valores cambia el análisis y por qué debemos documentar esas decisiones.
