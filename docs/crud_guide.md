# Cómo funciona el CRUD

El CRUD es una API que permanece disponible mientras el servidor FastAPI esté en ejecución. Cada solicitud HTTP ejecuta una operación independiente. Se pueden crear, consultar, actualizar y eliminar tantos documentos como se necesite, sin reiniciar el programa. Los datos se almacenan en MongoDB y permanecen después de cerrar el servidor.

## Recorrido de una solicitud

1. `app/routes/listens.py` recibe el método HTTP, la ruta y los parámetros.
2. `app/models.py` valida los campos con Pydantic. Si son incorrectos, responde 422 antes de escribir en MongoDB.
3. `app/services/listen_service.py` interpreta el identificador, prepara filtros y determina la operación.
4. `app/repositories/listen_repository.py` ejecuta la operación PyMongo sobre `listenbrainz_db.listens`.
5. La respuesta validada devuelve el identificador como una cadena JSON.

## Demostración en Swagger

Iniciar con `.\.venv\Scripts\python.exe -m scripts.run_api --reload` y abrir http://127.0.0.1:8000/docs.

### Crear dos reproducciones

Abrir `POST /listens`, pulsar **Try it out** y ejecutar:

```json
{
  "user_name": "classroom_demo",
  "timestamp": 1793318246,
  "track_metadata": {
    "track_name": "First demonstration",
    "artist_name": "Demonstration artist"
  }
}
```

La respuesta 201 devuelve un `id`. Guardarlo. Repetir con otra canción: se obtiene otro identificador y ambos documentos permanecen guardados. No se eliminan automáticamente los documentos creados desde Swagger.

### Consultar y filtrar

En `GET /listens`, escribir `classroom_demo` en `user_name`. Usar `limit=1` y cambiar `page` entre 1 y 2 para ver las dos reproducciones. Probar `artist_name`, `start_timestamp`, `end_timestamp`, `sort_by` y `sort_order`.

En `GET /listens/{listen_id}`, introducir uno de los identificadores guardados para consultar ese documento exacto.

### Actualizar un campo

En `PATCH /listens/{listen_id}`, usar uno de los identificadores creados y enviar:

```json
{
  "track_metadata": {
    "track_name": "Updated demonstration"
  }
}
```

Solo cambia el nombre de esa canción. El artista, el usuario y los demás metadatos permanecen. La respuesta es 200. Volver a consultar el documento confirma la persistencia del cambio.

`PUT /listens/{listen_id}` recibe el mismo cuerpo completo que POST y reemplaza el contenido de la reproducción, conservando su identificador. Los campos opcionales no incluidos en PUT dejan de formar parte del documento. Ninguna actualización crea documentos cuando el identificador no existe: responde 404.

### Eliminar una reproducción de prueba

En `DELETE /listens/{listen_id}`, usar exclusivamente un identificador creado durante la demostración. La respuesta 204 no contiene cuerpo. Una consulta posterior devuelve 404. El otro documento de prueba sigue disponible hasta que se elimine explícitamente.

## Qué significa el bloque de limpieza

`scripts/demo_crud.py` es un cliente de prueba de la API. Su bloque `finally` elimina los documentos que ese cliente creó, incluso si la demostración falla. No implementa el CRUD del servidor ni limita la API a una sola ejecución. Con `--rounds 3`, realiza tres rondas de solicitudes HTTP sobre documentos distintos. Las pruebas automatizadas usan la misma precaución para no dejar registros temporales.

## Prueba con la colección ampliada

Las consultas, los índices y el CRUD apuntan a la misma colección de datos reales. Las pruebas de escritura crean documentos propios y eliminan únicamente esos identificadores. Los registros reales se utilizan para comprobar consultas, estadísticas y planes de ejecución sin modificarlos. El objetivo de cuatro millones representa el total de la colección, incluidos los 50 000 originales.
