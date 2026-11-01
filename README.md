Aquí tienes el contenido listo para copiar y pegar en tu archivo `README.md` de GitHub.

# 🎵 ListenBrainz — Módulo MongoDB

## 📌 Descripción del proyecto

Este proyecto forma parte de un sistema de Big Data orientado al almacenamiento y análisis de reproducciones musicales reales obtenidas de **ListenBrainz**.

El módulo de MongoDB se encarga de almacenar información musical semiestructurada, realizar operaciones CRUD y ejecutar la inserción automatizada de grandes cantidades de registros mediante Python y PyMongo.

## 🎯 Objetivos

El desarrollo se centra en tres entregables principales:

1. **Modelado documental:** diseñar una estructura adecuada para almacenar los registros musicales en MongoDB.
2. **CRUD completo:** implementar las operaciones Create, Read, Update y Delete.
3. **Inserción por lotes:** desarrollar un script en Python para cargar eficientemente 50 000 registros musicales.

## 🗄️ 1. Modelado documental

Se utilizó MongoDB debido a su capacidad para almacenar documentos JSON con estructuras anidadas y campos variables.

**Configuración de la base de datos:**

- Base de datos: `listenbrainz_db`
- Colección: `listens`
- Formato de origen: JSONL
- Cantidad de registros: 50 000

Cada documento representa una reproducción musical e incluye información del usuario, fecha de reproducción, canción, artista, álbum y metadatos adicionales.

### Ejemplo de documento

```
{
  "user_id": 86100,
  "user_name": "Xizonic",
  "timestamp": 1793318246,
  "track_metadata": {
    "track_name": "Only",
    "artist_name": "NF & Sasha Sloan",
    "release_name": "The Search",
    "additional_info": {
      "duration_ms": 225470,
      "submission_client": "navidrome"
    }
  },
  "recording_msid": "14000594-d193-4959-b590-37fa67449096"
}
```

La estructura documental permite conservar los metadatos originales sin dividirlos en múltiples tablas.

## 🔄 2. Operaciones CRUD

Se implementaron las cuatro operaciones fundamentales de MongoDB.

| Operación | Descripción                                    | Método        |
| --------- | ---------------------------------------------- | ------------- |
| CREATE    | Insertar un documento musical                  | `insertOne()` |
| READ      | Consultar reproducciones por usuario o artista | `find()`      |
| UPDATE    | Actualizar información de una canción          | `updateOne()` |
| DELETE    | Eliminar un documento de prueba                | `deleteOne()` |

Las operaciones se ejecutaron utilizando documentos de prueba para preservar la integridad de los registros originales.

**Archivo:** `crud.mongodb.js`

## ⚙️ 3. Inserción por lotes

Se desarrolló un script en Python utilizando **PyMongo** para importar los registros desde un archivo JSONL hacia MongoDB.

El programa lee los registros secuencialmente, valida su estructura y realiza inserciones agrupadas.

**Resultados de la carga inicial:**

- Registros insertados: **50 000**
- Tamaño de lote: **1 000 documentos**
- Total de lotes: **50**
- Registros inválidos: **0**

El importador también incorpora mecanismos para reconocer registros previamente cargados y evitar duplicaciones en futuras ejecuciones.

**Archivo:** `importar.py`

## 🔎 4. Índices y consultas

Se implementaron índices para optimizar las búsquedas:

- `user_name`: consultas por usuario.
- `track_metadata.artist_name`: consultas por artista.
- `timestamp`: ordenamiento por fecha de reproducción.

Además, se desarrollaron consultas analíticas para identificar artistas más escuchados, canciones populares, usuarios activos y reproducciones agrupadas por fecha.

**Archivos:** `indices.mongodb.js` y `consultas.mongodb.js`

## 📊 5. Resultados obtenidos

| Indicador                               | Resultado |
| --------------------------------------- | --------- |
| Reproducciones almacenadas              | 50 000    |
| Usuarios únicos                         | 1 935     |
| Artistas únicos                         | 8 554     |
| Registros inválidos en la carga inicial | 0         |
| Índices personalizados                  | 3         |

Las verificaciones confirmaron la conservación de los 50 000 documentos y el funcionamiento de las operaciones CRUD.

## 🛠️ 6. Tecnologías utilizadas

- **MongoDB:** almacenamiento documental.
- **MongoDB Shell (mongosh):** administración y consultas.
- **Python 3.12:** procesamiento de registros.
- **PyMongo:** conexión e inserción de documentos.
- **JSONL:** formato del dataset.
- **Git y GitHub:** control de versiones.

## 📁 7. Estructura del proyecto

```
ListenBrainz_Proyecto/
├── data/
├── importar.py
├── crud.mongodb.js
├── indices.mongodb.js
├── consultas.mongodb.js
├── verificar.py
├── requirements.txt
├── README.md
└── evidencias/
```

El dataset completo se mantiene localmente debido a su tamaño.

## ▶️ 8. Ejecución

Instalar las dependencias:

```
python -m pip install -r requirements.txt
```

Verificar los registros almacenados:

```
python verificar.py
```

Ejecutar las operaciones CRUD:

```
mongosh "mongodb://localhost:27017/listenbrainz_db" --file crud.mongodb.js
```

Ejecutar las consultas analíticas:

```
mongosh "mongodb://localhost:27017/listenbrainz_db" --file consultas.mongodb.js
```

**Nota:** el script `importar.py` se utiliza para la carga inicial o futuras importaciones deliberadas. No es necesario volver a ejecutarlo para consultar los 50 000 registros existentes.

## 📚 9. Fuente de datos

Los datos fueron obtenidos de los volcados oficiales de ListenBrainz.

- [ListenBrainz — Descarga de datos](https://listenbrainz.org/data/)
- [Documentación oficial de ListenBrainz Dumps](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)

## ✅ 10. Conclusiones

El módulo de MongoDB cumple con los tres entregables asignados: **modelado documental, CRUD completo e inserción por lotes**.

Se logró almacenar y verificar 50 000 reproducciones musicales reales, conservar su estructura semiestructurada y desarrollar consultas para analizar los datos.

La implementación permite gestionar registros musicales de manera organizada y constituye una base para la integración con los demás componentes del proyecto de Big Data.

Añade una sección de instalación de MongoDB