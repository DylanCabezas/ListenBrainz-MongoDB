{
    const coleccion = db.getSiblingDB("listenbrainz_db").getCollection("listens");
    for (const clave of [{user_name: 1}, {"track_metadata.artist_name": 1}, {timestamp: -1}]) {
        const encontrado = coleccion.getIndexes().find(indice =>
            JSON.stringify(indice.key) === JSON.stringify(clave) &&
            !indice.hidden && !indice.sparse && !indice.partialFilterExpression
        );
        if (encontrado) print("Índice disponible: " + encontrado.name);
        else print("Índice creado: " + coleccion.createIndex(clave));
    }
    printjson(coleccion.getIndexes());
    const ejemplo = coleccion.findOne({es_prueba: {$ne: true}});
    if (!ejemplo) throw new Error("No hay documentos para explicar consultas.");
    const consultas = [
        ["Usuario", coleccion.find({user_name: ejemplo.user_name}).limit(10)],
        ["Artista", coleccion.find({"track_metadata.artist_name": ejemplo.track_metadata.artist_name}).limit(10)],
        ["Recientes", coleccion.find({}).sort({timestamp: -1}).limit(10)]
    ];
    function etapas(nodo, resultado = []) {
        if (nodo && typeof nodo === "object") {
            if (nodo.stage) resultado.push(nodo.stage);
            for (const valor of Object.values(nodo)) etapas(valor, resultado);
        }
        return resultado;
    }
    for (const [nombre, cursor] of consultas) {
        const explicacion = cursor.explain("executionStats");
        const estadisticas = explicacion.executionStats || {};
        const plan = etapas(explicacion.queryPlanner.winningPlan);
        printjson({
            consulta: nombre, etapas: plan,
            acceso: plan.includes("IXSCAN") ? "IXSCAN" : plan.includes("COLLSCAN") ? "COLLSCAN" : "Consultar etapas",
            totalDocsExamined: estadisticas.totalDocsExamined,
            totalKeysExamined: estadisticas.totalKeysExamined,
            executionTimeMillis: estadisticas.executionTimeMillis
        });
    }
}
