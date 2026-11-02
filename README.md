# ListenBrainz: API con Python y MongoDB

API REST para guardar, consultar, actualizar y eliminar reproducciones musicales. Está desarrollada con Python 3.12, FastAPI, Pydantic y PyMongo.

Los datos se guardan en la base `listenbrainz_db`, colección `listens`. Actualmente contiene **4 millones de reproducciones reales de ListenBrainz**. Los 50 000 registros originales se conservaron sin cambios.

## 1. Iniciar la API

Necesitas Python 3.12 y MongoDB local en ejecución.

Desde la terminal **Git Bash de Visual Studio Code**, ubicada en la carpeta del proyecto, ejecuta:

```bash
./.venv/Scripts/python.exe main.py
```

Si es la primera instalación, crea el entorno e instala las dependencias antes de iniciar:

```bash
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Abre **http://127.0.0.1:8000/docs** para probar la API desde Swagger. Mantén la terminal abierta; para detener el servidor, pulsa **Ctrl + C**.

La dirección `http://127.0.0.1:8000/` devuelve `Not Found` porque no tiene una ruta definida. Utiliza `/docs` o `/listens`.

La conexión predeterminada es `mongodb://localhost:27017/`. Se puede cambiar con la variable de entorno `MONGO_URI`. La API está preparada para uso local y no incluye autenticación.

## 2. Usar el CRUD

CRUD significa crear, consultar, actualizar y eliminar. Cada solicitud es independiente: puedes realizar varias operaciones sobre distintos documentos sin reiniciar el servidor.

| Método | Ruta | Qué hace |
| --- | --- | --- |
| POST | `/listens` | Crea una reproducción |
| GET | `/listens` | Consulta con filtros y páginas |
| GET | `/listens/{listen_id}` | Consulta una reproducción por su identificador |
| PATCH | `/listens/{listen_id}` | Cambia los campos enviados |
| PUT | `/listens/{listen_id}` | Reemplaza el contenido completo |
| DELETE | `/listens/{listen_id}` | Elimina una reproducción |
| GET | `/listens/feed` | Recorre los resultados usando un cursor |
| GET | `/listens/stats/summary` | Muestra reproducciones y usuarios únicos |
| GET | `/listens/stats/top-artists` | Muestra los artistas más escuchados |

En Swagger, abre **POST /listens**, pulsa **Try it out**, pega este ejemplo y pulsa **Execute**:

```json
{
  "user_name": "demo_user",
  "timestamp": 1793318246,
  "track_metadata": {
    "track_name": "Demo song",
    "artist_name": "Demo artist"
  }
}
```

La respuesta devuelve un `id`. Utilízalo para consultar, actualizar o eliminar ese documento de prueba. Para cambiar solamente la canción con PATCH:

```json
{"track_metadata": {"track_name": "Updated song"}}
```

Los documentos creados desde Swagger permanecen guardados hasta que los elimines. La guía completa está en [docs/crud_guide.md](docs/crud_guide.md).

### Filtros y páginas

Las consultas aceptan `user_name`, `artist_name`, `start_timestamp` y `end_timestamp`. Las fechas son segundos Unix y los nombres se comparan exactamente.

Ejemplo:

```text
http://127.0.0.1:8000/listens?user_name=demo_user&page=1&limit=10
```

Puedes ordenar con `sort_by` y `sort_order=asc` o `desc`. El límite máximo es de 100 documentos por solicitud. Para recorrer muchos resultados, usa `/listens/feed` y envía el `next_cursor` recibido en la siguiente solicitud, manteniendo los mismos filtros.

Las respuestas principales son: **200** operación correcta, **201** creación, **204** eliminación, **400** parámetros incoherentes o identificador inválido, **404** documento inexistente, **422** datos inválidos y **503** error de MongoDB.

## 3. Ejecutar las pruebas

Con la API iniciada, abre otra terminal Git Bash y ejecuta tres rondas CRUD:

```bash
./.venv/Scripts/python.exe -m scripts.demo_crud --rounds 3
```

Cada ronda crea, consulta, actualiza y elimina su propio documento de prueba.

Para ejecutar las pruebas automatizadas, sin necesidad de iniciar el servidor:

```bash
./.venv/Scripts/python.exe -m pytest -q
```

Para incluir la prueba sobre MongoDB real:

```bash
RUN_MONGO_TESTS=1 ./.venv/Scripts/python.exe -m pytest -q
```

La prueba real elimina únicamente sus documentos temporales. Ejecútala cuando no haya importaciones ni otras escrituras simultáneas.

La validación realizada terminó con **12 pruebas aprobadas**, tres rondas CRUD correctas y cuatro consultas que utilizaron índices. Detalles en [evidencias/final_validation.md](evidencias/final_validation.md).

## 4. Importar datos

**Los cuatro millones ya están cargados. No necesitas volver a importarlos para usar la API.**

El importador lee archivos reales de [ListenBrainz](https://listenbrainz.org/data/) línea por línea, inserta por lotes, evita duplicados y guarda el avance para poder continuar después de una interrupción. Usa SQLite únicamente para guardar ese control; las reproducciones se almacenan en MongoDB.

Para simular la lectura de 1000 líneas sin insertar:

```bash
./.venv/Scripts/python.exe -m scripts.import_listens --limit 1000
```

Para una carga pequeña, añade `--apply`. Para cargar hasta un total de cuatro millones:

```bash
./.venv/Scripts/python.exe -m scripts.import_listens --full --apply --target 4000000
```

El objetivo incluye los registros existentes. Puedes indicar otro archivo con `--source "ruta/archivo.listens"`. Los archivos comprimidos deben extraerse antes. Repetir el comando reanuda la carga; no ejecutes varios importadores a la vez ni modifiques el archivo de origen durante el proceso.

El estado se guarda en `data/import_state.sqlite3` y las líneas inválidas en `data/import_state.errors.jsonl`. La carga realizada insertó 3 950 000 documentos nuevos, reconoció los 50 000 existentes y no registró líneas inválidas.

## 5. Organización del proyecto

| Archivo o carpeta | Responsabilidad |
| --- | --- |
| `main.py` | Iniciar el servidor |
| `app/config.py` | Configuración de MongoDB |
| `app/database.py` | Conexión e índices |
| `app/models.py` | Validación de datos |
| `app/errors.py` | Errores propios de la aplicación |
| `app/main.py` | Configuración de FastAPI y manejo de errores |
| `app/routes/listens.py` | Endpoints HTTP |
| `app/services/` | Lógica del CRUD y de la importación |
| `app/repositories/` | Operaciones PyMongo |
| `scripts/` | Demostraciones, consultas y verificaciones |
| `tests/` | Pruebas automatizadas |
| `evidencias/` | Resultados de las comprobaciones |

Para verificar índices o consultar estadísticas desde Python:

```bash
./.venv/Scripts/python.exe -m scripts.verify_indexes
./.venv/Scripts/python.exe -m scripts.queries
```

El código principal está en `app/`. `main.py` inicia la API y `scripts/` contiene las herramientas de apoyo. Las evidencias finales y el registro de importación se conservan en `evidencias/`.
