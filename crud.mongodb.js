{
    const base = db.getSiblingDB("listenbrainz_db");
    const coleccion = base.getCollection("listens");
    const filtro = {_id: "listenbrainz:prueba:crud:v1", user_name: "usuario_prueba_crud", es_prueba: true};
    const existente = coleccion.findOne({_id: filtro._id});
    if (existente && (existente.user_name !== filtro.user_name || existente.es_prueba !== true)) {
        throw new Error("El identificador reservado pertenece a otro documento; operación cancelada.");
    }
    const totalAntes = coleccion.countDocuments({});
    try {
        print("CREATE");
        printjson(coleccion.updateOne(filtro, {$setOnInsert: {
            timestamp: Math.floor(Date.now() / 1000),
            track_metadata: {track_name: "Canción de prueba CRUD", artist_name: "Artista de prueba CRUD"}
        }}, {upsert: true}));
        print("READ: usuario, artista y canción con proyección y límite");
        for (const consulta of [
            {user_name: filtro.user_name, _id: filtro._id},
            {"track_metadata.artist_name": "Artista de prueba CRUD", _id: filtro._id},
            {"track_metadata.track_name": "Canción de prueba CRUD", _id: filtro._id}
        ]) {
            printjson(coleccion.find(consulta, {_id: 0, user_name: 1, track_metadata: 1}).limit(5).toArray());
        }
        print("UPDATE");
        const resultado = coleccion.updateOne(filtro, {$set: {
            "track_metadata.track_name": "Canción actualizada CRUD",
            "track_metadata.artist_name": "Artista actualizado CRUD"
        }});
        printjson(resultado);
        const actualizado = coleccion.findOne(filtro);
        if (!actualizado || actualizado.track_metadata.track_name !== "Canción actualizada CRUD" ||
            actualizado.track_metadata.artist_name !== "Artista actualizado CRUD") {
            throw new Error("No se verificó la actualización.");
        }
        printjson(actualizado);
    } finally {
        print("DELETE");
        printjson(coleccion.deleteOne(filtro));
        if (coleccion.countDocuments(filtro) !== 0) throw new Error("La limpieza falló.");
    }
    const totalDespues = coleccion.countDocuments({});
    printjson({totalAntes, totalDespues, pruebaEliminada: true});
    if (totalDespues !== totalAntes - (existente ? 1 : 0)) throw new Error("Conteo final inesperado.");
}
