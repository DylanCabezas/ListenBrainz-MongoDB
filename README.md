# ListenBrainz: API REST con Python y MongoDB

El módulo permite gestionar reproducciones reales mediante HTTP, con FastAPI, Pydantic y PyMongo. Utiliza `listenbrainz_db.listens`. El servidor mantiene el CRUD disponible para múltiples solicitudes; no ejecuta una secuencia automática de creación, actualización y eliminación al iniciarse.

Las funciones, clases, variables, módulos nuevos y endpoints tienen nombres en inglés. Los archivos JavaScript anteriores están archivados en `legacy/mongodb/` y no intervienen en la ejecución. Los datos y los otros componentes del proyecto se conservan.

## Resultado verificado

La carga autorizada y las pruebas finalizaron el 1 de noviembre de 2026:

| Comprobación | Resultado |
| --- | --- |
| Reproducciones reales almacenadas | 4 000 000 |
| Nuevas reproducciones insertadas | 3 950 000 |
| Registros originales conservados sin cambios | 50 000 |
| Usuarios únicos | 25 550 |
| Líneas inválidas durante la carga | 0 |
| Pruebas automatizadas con integración real | 12 aprobadas |
| Rondas CRUD por HTTP | 3 aprobadas |
| Planes de consulta con IXSCAN | 4 de 4 |

El conteo fue de cuatro millones antes y después de las pruebas. Las evidencias reproducibles están en [evidencias/final_validation.md](evidencias/final_validation.md). La dependencia Starlette emitió una advertencia de deprecación sobre httpx en TestClient; las pruebas finalizaron sin errores.

## Instalar e iniciar

Requisitos: Python 3.12 y MongoDB Community Server local iniciado en el puerto 27017.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Abrir **http://127.0.0.1:8000/docs**. Desde Swagger se pueden enviar solicitudes sucesivas y gestionar documentos por su identificador. Para recarga automática durante el desarrollo:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_api --reload
```

La conexión predeterminada es `mongodb://localhost:27017/`; se puede cambiar mediante la variable de entorno `MONGO_URI`. La base y la colección permanecen fijas. La API está orientada a la demostración local y no incorpora autenticación.

## Cómo funciona el CRUD

La explicación y la demostración paso a paso están en [docs/crud_guide.md](docs/crud_guide.md).

| Método | Endpoint | Operación |
| --- | --- | --- |
| POST | `/listens` | Crear una reproducción; devuelve 201 e `id` |
| GET | `/listens` | Consultar con filtros y páginas |
| GET | `/listens/feed` | Consultar con cursor, sin desplazamientos ni conteo global |
| GET | `/listens/{listen_id}` | Consultar un documento |
| PATCH | `/listens/{listen_id}` | Cambiar solamente los campos enviados |
| PUT | `/listens/{listen_id}` | Reemplazar el documento conservando su identificador |
| DELETE | `/listens/{listen_id}` | Eliminar un documento; devuelve 204 |
| GET | `/listens/stats/summary` | Contar reproducciones y usuarios únicos |
| GET | `/listens/stats/top-artists` | Consultar artistas más escuchados |

Ejemplo de cuerpo para POST o PUT:

```json
{
  "user_name": "classroom_demo",
  "timestamp": 1793318246,
  "track_metadata": {
    "track_name": "Demonstration",
    "artist_name": "Demonstration artist",
    "additional_info": {"duration_ms": 180000}
  }
}
```

Ejemplo de PATCH, usando el identificador devuelto por POST:

```json
{"track_metadata": {"track_name": "Updated demonstration"}}
```

PATCH conserva los campos no enviados, incluidos los metadatos adicionales anidados. Enviar un objeto vacío como `additional_info` lo vacía explícitamente. PUT requiere los mismos campos que POST y reemplaza el contenido completo. Las actualizaciones no hacen inserciones implícitas.

Las rutas de lista, cursor y estadísticas admiten `user_name`, `artist_name`, `start_timestamp` y `end_timestamp`. Las fechas son segundos Unix y ambos extremos se incluyen. Los nombres se comparan exactamente.

`GET /listens` acepta `page` (1–10000), `limit` (1–100), `sort_by` (`timestamp`, `user_name` o `track_metadata.artist_name`) y `sort_order` (`asc` o `desc`). La respuesta contiene `items`, `page`, `limit` y `total`.

Para recorrer millones de documentos, utilizar `/listens/feed?limit=100`: la respuesta contiene `items` y `next_cursor`. Enviar el cursor devuelto en la siguiente solicitud, manteniendo los mismos filtros. `next_cursor=null` indica el final. El orden es fecha descendente e identificador descendente, compatible con ObjectId y los identificadores históricos de texto. Este recorrido evita el coste creciente de `skip` y no calcula un total por página. No representa una instantánea: las escrituras concurrentes pueden alterar el conjunto consultado.

Los artistas más escuchados aceptan `limit` de 1 a 100. Las estadísticas son exactas y pueden tardar al procesar toda la colección.

Respuestas: 200 para lecturas y actualizaciones, 201 para inserciones, 204 para eliminaciones, 400 para identificadores, cursores o rangos inválidos, 404 para documentos ausentes, 422 para cuerpos y parámetros incorrectos y 503 para errores de MongoDB. ObjectId se devuelve como una cadena JSON `id`; también se admiten identificadores `listenbrainz:...` de importaciones anteriores.

## Demostración repetible y pruebas

Con el servidor iniciado, ejecutar en otra terminal:

```powershell
.\.venv\Scripts\python.exe -m scripts.demo_crud --rounds 3
```

Ese script es un cliente HTTP de prueba. Cada ronda crea un documento distinto, lo consulta, lo actualiza y elimina únicamente su propio documento. Su bloque de limpieza no es la implementación del CRUD: el servidor permanece disponible para cualquier otra solicitud. Los documentos creados desde Swagger permanecen hasta que se eliminen explícitamente.

Pruebas aisladas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Prueba adicional en MongoDB real, con documentos propios y limpieza por identificador:

```powershell
$env:RUN_MONGO_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:RUN_MONGO_TESTS
```

Ejecutar la prueba de conteo final cuando no haya una importación u otras escrituras concurrentes. Para comprobar Swagger, consultas y estadísticas con conexión real:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_api
```

Cuando la colección tenga exactamente cuatro millones y no haya otras escrituras, se pueden repetir todas las comprobaciones y generar las evidencias finales con `.\.venv\Scripts\python.exe -m scripts.validate_project`.

## Importación real hasta cuatro millones

La carga es explícita y no se inicia al arrancar FastAPI. Lee el archivo local `10.listens`, del volcado real de [ListenBrainz](https://listenbrainz.org/data/), secuencialmente y con lotes de 1000 documentos. Los archivos comprimidos deben extraerse antes. No genera datos artificiales.

Simular 1000 líneas:

```powershell
.\.venv\Scripts\python.exe -m scripts.import_listens --limit 1000
```

Insertar una carga pequeña y confirmar su resultado:

```powershell
.\.venv\Scripts\python.exe -m scripts.import_listens --limit 1000 --apply
```

Cargar hasta un total de cuatro millones, incluidos los registros existentes:

```powershell
.\.venv\Scripts\python.exe -u -m scripts.import_listens --full --apply --target 4000000 --batch-size 1000
```

Si hay varios archivos, indicar `--source "ruta/al/archivo.listens"`. Repetir el comando reanuda desde el último lote confirmado. No ejecutar importadores concurrentes ni modificar el origen durante la carga.

El estado SQLite en `data/import_state.sqlite3` conserva huellas SHA-256 y posiciones en bytes. Al iniciar, el importador recorre los documentos existentes con cursor por lotes para reconocerlos sin modificarlos. Solo mantiene un lote en memoria; las huellas se almacenan en disco. Los documentos idénticos, excluyendo `_id`, se omiten. Los nuevos documentos importados tienen identificadores deterministas para impedir duplicaciones después de una interrupción. Los documentos creados por la API utilizan ObjectId.

Las líneas inválidas se registran con origen y posición en `data/import_state.errors.jsonl`. Los errores de escritura distintos de duplicados detienen la carga sin avanzar el punto de reanudación del lote fallido. Corregir la causa y repetir el comando. El resultado indica `total`, `target_reached` y `source_exhausted`; si el origen se agota antes del objetivo, hacen falta otros archivos reales. No se borran duplicados históricos ni registros originales.

La ejecución autorizada está registrada en `evidencias/import_4m_progress.txt`. El resultado final y las pruebas sobre la colección ampliada se documentan en `evidencias/final_validation.md`. El objetivo se alcanzó antes de agotar el archivo de origen; no se importaron los registros restantes.

## Índices, consultas y conservación de originales

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_indexes
.\.venv\Scripts\python.exe -m scripts.queries --artist-name "NF & Sasha Sloan"
.\.venv\Scripts\python.exe -m scripts.baseline
.\.venv\Scripts\python.exe -m scripts.verify_dataset
```

Los índices compuestos cubren fecha e identificador, usuario y fecha, y artista y fecha. Se conservan los índices previos. El verificador ejecuta `explain` con `executionStats`, sin `hint`, y exige `IXSCAN` en las consultas principales. Otros ordenamientos o combinaciones de filtros pueden requerir procesamiento adicional.

`data/original_baseline.jsonl` conserva los identificadores y las huellas de los 50 000 originales. La verificación los consulta por lotes mediante el índice `_id` y compara su contenido y multiplicidad con el dataset inicial, sin cargar la colección de millones de documentos en memoria. La línea base existente no se sobrescribe.

## Estructura

```text
app/
  config.py
  database.py
  errors.py
  main.py
  models.py
  repositories/listen_repository.py
  routes/listens.py
  services/listen_service.py
  services/import_service.py
scripts/
  run_api.py
  demo_crud.py
  import_listens.py
  queries.py
  baseline.py
  verify_dataset.py
  verify_indexes.py
  smoke_api.py
  validate_project.py
tests/
docs/crud_guide.md
main.py
requirements.txt
```

`importar.py` y `verificar.py` se mantienen como entradas compatibles a las implementaciones nuevas. Los archivos históricos y evidencias previas se conservan. El módulo no modifica Neo4j, Cassandra, Airflow ni dashboard y no ejecuta eliminaciones de bases o colecciones.
