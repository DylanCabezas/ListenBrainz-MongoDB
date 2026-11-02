# Validación de la API REST

Esta es una evidencia histórica previa a la carga completa. El resultado vigente sobre cuatro millones de reproducciones está en `final_validation.md`.

Validación ejecutada el 1 de noviembre de 2026 con Python 3.12.2 y MongoDB local.

- Pruebas automatizadas con `RUN_MONGO_TESTS=1`: **7 aprobadas**.
- CRUD HTTP consecutivo sobre dos documentos temporales en la colección real: aprobado; limpieza por sus identificadores.
- Validación de entradas, filtros, paginación, estadísticas e identificadores históricos: aprobada.
- Importador: simulación, deduplicación, reanudación, objetivo máximo y recuperación tras escritura parcial: aprobados.
- Simulación del archivo real `10.listens`: 1000 líneas procesadas, 1000 duplicadas, 0 inválidas, 0 insertadas.
- Verificador histórico: 50 000 documentos, 1935 usuarios, 0 documentos de prueba y 0 originales faltantes al comparar las huellas y multiplicidades con el dataset inicial.
- Índices: `IXSCAN` en las tres consultas verificadas con `executionStats`, sin `hint`. Consulta reciente: 20 claves y 20 documentos examinados; usuario de muestra: 1 y 1; artista de muestra: 1 y 1.
- Dependencias: `pip check` sin conflictos.
- Aplicación con conexión real: `/docs`, `/openapi.json`, lista paginada, resumen y artistas devolvieron 200. Resumen: 50 000 reproducciones y 1935 usuarios únicos.
- La carga completa no se ejecutó.

La versión instalada de Starlette emitió una advertencia de deprecación sobre el uso de httpx en TestClient; no afecta los resultados anteriores.

Comandos para reproducir las comprobaciones en README.md. No se eliminaron documentos originales ni se ejecutaron operaciones de eliminación de bases o colecciones.

## Flujo íntegro en Python

Se incorporaron `scripts.run_api`, `scripts.demo_crud`, `scripts.queries` y `scripts.baseline`. La ejecución ya no requiere mongosh ni Node.js. Los archivos JavaScript anteriores se conservan como antecedentes.

La demostración Python se ejecutó contra FastAPI en el puerto temporal 8011 durante tres rondas. En cada ronda se verificaron CREATE 201, READ 200, UPDATE 200, DELETE 204 y ausencia posterior con 404. El servidor temporal se detuvo al finalizar. Después, las siete pruebas automatizadas volvieron a aprobarse y el conteo real permaneció en 50 000.

Las consultas analíticas migradas se ejecutaron completas sobre MongoDB local. Resultados en `python_queries.txt`; planes de índices en `python_indexes.txt`; rondas CRUD en `python_crud.txt`.
