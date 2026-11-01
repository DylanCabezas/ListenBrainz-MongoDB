import hashlib
import json
from collections import Counter
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import BulkWriteError, PyMongoError


def huella(documento):
    contenido = {clave: valor for clave, valor in documento.items() if clave != "_id"}
    return hashlib.sha256(json.dumps(contenido, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validar(documento):
    if not isinstance(documento, dict) or "_id" in documento:
        return False
    metadata = documento.get("track_metadata")
    return (
        isinstance(documento.get("user_name"), str)
        and bool(documento["user_name"].strip())
        and type(documento.get("timestamp")) is int
        and 0 <= documento["timestamp"] <= 253402300799
        and isinstance(metadata, dict)
        and all(isinstance(metadata.get(campo), str) and metadata[campo].strip() for campo in ("track_name", "artist_name"))
        and ("additional_info" not in metadata or isinstance(metadata["additional_info"], dict))
    )


def insertar_lote(coleccion, lote):
    try:
        return len(coleccion.insert_many(lote, ordered=False).inserted_ids)
    except BulkWriteError as error:
        if error.details.get("writeConcernErrors") or any(item["code"] != 11000 for item in error.details.get("writeErrors", [])):
            raise
        return error.details["nInserted"]


def main():
    archivos = sorted((Path(__file__).resolve().parent / "data").rglob("listenbrainz_50000.jsonl"))
    if len(archivos) != 1:
        raise RuntimeError(f"Se esperaba un único dataset; encontrados: {len(archivos)}")
    insertados = invalidos = omitidos = validos = 0
    with MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000) as cliente:
        cliente.admin.command("ping")
        coleccion = cliente.listenbrainz_db.listens
        existentes = Counter()
        for documento in coleccion.find({}):
            existentes[huella(documento)] += 1
        ocurrencias = Counter()
        lote = []
        print(f"Dataset: {archivos[0]} | Documentos existentes: {sum(existentes.values())}")
        with archivos[0].open(encoding="utf-8-sig") as archivo:
            for numero, linea in enumerate(archivo, 1):
                try:
                    documento = json.loads(linea)
                    if not validar(documento):
                        raise ValueError("Estructura o campos obligatorios inválidos")
                    firma = huella(documento)
                except (ValueError, TypeError) as error:
                    invalidos += 1
                    print(f"Línea {numero} inválida: {error}")
                    continue
                validos += 1
                ocurrencias[firma] += 1
                if ocurrencias[firma] <= existentes[firma]:
                    omitidos += 1
                else:
                    documento["_id"] = f"listenbrainz:{firma}:{ocurrencias[firma]}"
                    lote.append(documento)
                if len(lote) == 1000:
                    insertados += insertar_lote(coleccion, lote)
                    lote.clear()
                    print(f"Línea {numero} | Insertados: {insertados} | Omitidos: {omitidos}")
                elif numero % 1000 == 0:
                    print(f"Línea {numero} | Insertados: {insertados} | Omitidos: {omitidos}")
        if lote:
            insertados += insertar_lote(coleccion, lote)
        print(f"Finalizado | Válidos: {validos} | Insertados: {insertados} | Omitidos: {omitidos} | Inválidos: {invalidos}")


if __name__ == "__main__":
    try:
        main()
    except (PyMongoError, OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"Importación detenida: {error}. Puede reanudar después de resolver la causa.")
