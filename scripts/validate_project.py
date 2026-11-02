import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from app.config import settings
from app.database import create_client


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidencias"


def run_check(name, arguments, environment):
    destination = EVIDENCE / f"final_{name}.txt"
    print(f"Running {name}", flush=True)
    with destination.open("w", encoding="utf-8") as stream:
        result = subprocess.run([sys.executable, *arguments], cwd=ROOT, env=environment,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"{name} failed; see {destination}")
    print(f"Passed {name}", flush=True)


def validate_http(environment):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with (EVIDENCE / "final_server.txt").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "scripts.run_api", "--port", str(port)],
            cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            url = f"http://127.0.0.1:{port}"
            for _ in range(150):
                if server.poll() is not None:
                    raise RuntimeError("Temporary API server exited before becoming ready")
                try:
                    with urlopen(f"{url}/openapi.json", timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(0.2)
            else:
                raise RuntimeError("Temporary API server did not become ready")
            run_check("http_crud", ["-m", "scripts.demo_crud", "--base-url", url, "--rounds", "3"], environment)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


def main():
    EVIDENCE.mkdir(exist_ok=True)
    environment = {**os.environ, "RUN_MONGO_TESTS": "1", "PYTHONIOENCODING": "utf-8"}
    with create_client() as client:
        collection = client[settings.database_name][settings.collection_name]
        before = collection.count_documents({})
        if before != 4000000:
            raise RuntimeError(f"Expected 4000000 listens before final validation, found {before}")
        run_check("tests", ["-m", "pytest", "-q"], environment)
        validate_http(environment)
        run_check("originals", ["-m", "scripts.verify_dataset"], environment)
        run_check("indexes", ["-m", "scripts.verify_indexes"], environment)
        run_check("api", ["-m", "scripts.smoke_api"], environment)
        run_check("queries", ["-m", "scripts.queries"], environment)
        after = collection.count_documents({})
        if after != before:
            raise RuntimeError(f"Final count changed from {before} to {after}")
        summary = {"validated_at": datetime.now(timezone(timedelta(hours=-5))).isoformat(),
                   "total_before": before, "total_after": after,
                   "http_crud_rounds": 3, "checks_passed": True}
        (EVIDENCE / "final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (EVIDENCE / "final_validation.md").write_text(
            "# Validación final del módulo MongoDB\n\n"
            f"Fecha de verificación: {summary['validated_at']}.\n\n"
            "- Colección real: **4 000 000 reproducciones**, antes y después de las pruebas.\n"
            "- Pruebas automatizadas, incluida integración MongoDB: aprobadas; salida en `final_tests.txt`.\n"
            "- Tres rondas CRUD sobre un servidor HTTP temporal: aprobadas; salida en `final_http_crud.txt`.\n"
            "- Los 50 000 originales se verificaron por identificador, contenido y multiplicidad; "
            "salida en `final_originals.txt`.\n"
            "- Cuatro consultas con índices y estadísticas reales de ejecución: "
            "salida en `final_indexes.txt`.\n"
            "- Swagger, OpenAPI, paginación y estadísticas con MongoDB real: "
            "salida en `final_api.txt`.\n"
            "- Consultas analíticas completas: salida en `final_queries.txt`.\n"
            "- La limpieza eliminó únicamente los documentos creados por las pruebas. "
            "No se eliminaron bases, colecciones ni documentos originales.\n\n"
            "La carga autorizada se conserva en `import_4m_progress.txt`. "
            "El servidor temporal de validación se detuvo al terminar. "
            "Para usar la API, ejecutar `python main.py` y abrir http://127.0.0.1:8000/docs.\n",
            encoding="utf-8",
        )
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
