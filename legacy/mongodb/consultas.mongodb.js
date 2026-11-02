{
    const coleccion = db.getSiblingDB("listenbrainz_db").getCollection("listens");
    const filtroReal = {es_prueba: {$ne: true}};
    const mostrar = (titulo, resultado) => {
        print(titulo);
        printjson(resultado);
    }
    const agregar = (titulo, etapas) => {
        mostrar(titulo, coleccion.aggregate([{$match: filtroReal}, ...etapas], {allowDiskUse: true}).toArray());
    }
    mostrar("Total de reproducciones", coleccion.countDocuments(filtroReal));
    mostrar("Usuarios únicos", coleccion.distinct("user_name", filtroReal).length);
    mostrar("Artistas únicos", coleccion.distinct("track_metadata.artist_name", filtroReal).length);
    agregar("Cinco artistas con más reproducciones", [
        {$group: {_id: "$track_metadata.artist_name", reproducciones: {$sum: 1}}},
        {$sort: {reproducciones: -1, _id: 1}}, {$limit: 5},
        {$project: {_id: 0, artista: "$_id", reproducciones: 1}}
    ]);
    agregar("Diez canciones más reproducidas por artista y canción", [
        {$group: {_id: {artista: "$track_metadata.artist_name", cancion: "$track_metadata.track_name"}, reproducciones: {$sum: 1}}},
        {$sort: {reproducciones: -1, "_id.artista": 1, "_id.cancion": 1}}, {$limit: 10},
        {$project: {_id: 0, artista: "$_id.artista", cancion: "$_id.cancion", reproducciones: 1}}
    ]);
    agregar("Cinco usuarios con más reproducciones", [
        {$group: {_id: "$user_name", reproducciones: {$sum: 1}}},
        {$sort: {reproducciones: -1, _id: 1}}, {$limit: 5},
        {$project: {_id: 0, usuario: "$_id", reproducciones: 1}}
    ]);
    mostrar("Diez reproducciones más recientes", coleccion.find(filtroReal,
        {_id: 0, user_name: 1, timestamp: 1, "track_metadata.artist_name": 1, "track_metadata.track_name": 1}
    ).sort({timestamp: -1}).limit(10).toArray());
    const artista = process.env.LISTENBRAINZ_ARTISTA || "NF & Sasha Sloan";
    mostrar("Reproducciones del artista: " + artista, coleccion.find(
        {...filtroReal, "track_metadata.artist_name": artista},
        {_id: 0, user_name: 1, timestamp: 1, track_metadata: 1}
    ).sort({timestamp: -1}).limit(10).toArray());
    agregar("Duración promedio por reproducción con duración numérica positiva", [
        {$match: {"track_metadata.additional_info.duration_ms": {$type: "number", $gt: 0}}},
        {$group: {_id: null, promedio_ms: {$avg: "$track_metadata.additional_info.duration_ms"}, muestras: {$sum: 1}}},
        {$project: {_id: 0, muestras: 1, promedio_ms: 1, promedio_segundos: {$divide: ["$promedio_ms", 1000]}}}
    ]);
    agregar("Reproducciones por día UTC", [
        {$match: {timestamp: {$type: "number"}}},
        {$project: {dia: {$dateToString: {format: "%Y-%m-%d", timezone: "UTC", date: {$toDate: {$multiply: ["$timestamp", 1000]}}}}}},
        {$group: {_id: "$dia", reproducciones: {$sum: 1}}},
        {$sort: {_id: 1}}, {$project: {_id: 0, dia: "$_id", reproducciones: 1}}
    ]);
}

