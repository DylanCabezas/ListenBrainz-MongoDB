import json
from collections import Counter
from pathlib import Path

from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from importar import huella, validar


def main():
    with MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000) as cliente:
        comprobaciones = {"conexion": cliente.admin.command("ping")["ok"] == 1}
        comprobaciones["base_existe"] = "listenbrainz_db" in cliente.list_database_names()
        base = cliente.listenbrainz_db
        comprobaciones["coleccion_existe"] = "listens" in base.list_collection_names()
        coleccion = base.listens
        total = coleccion.count_documents({})
        print(f"Documentos: {total}")
        comprobaciones["al_menos_50000"] = total >= 50000
        print("Documento real:")
        print(json_util.dumps(coleccion.find_one({"es_prueba": {"$ne": True}}), indent=2, ensure_ascii=False))
        indices = list(coleccion.list_indexes())
        print("Índices:")
        print(json_util.dumps(indices, indent=2, ensure_ascii=False))
        for campo, orden in (("user_name", 1), ("track_metadata.artist_name", 1), ("timestamp", -1)):
            comprobaciones[f"indice_{campo}"] = any(
                list(indice["key"].items()) == [(campo, orden)]
                and not indice.get("hidden") and not indice.get("sparse")
                and not indice.get("partialFilterExpression") for indice in indices
            )
        print(f"Usuarios únicos: {len(coleccion.distinct('user_name'))}")
        pruebas = coleccion.count_documents({"$or": [{"es_prueba": True}, {"user_name": "usuario_prueba_crud"}]})
        print(f"Documentos de prueba: {pruebas}")
        comprobaciones["sin_pruebas"] = pruebas == 0
        archivos = list((Path(__file__).resolve().parent / "data").rglob("listenbrainz_50000.jsonl"))
        comprobaciones["dataset_unico"] = len(archivos) == 1
        if len(archivos) == 1:
            originales = Counter()
            invalidos = 0
            with archivos[0].open(encoding="utf-8-sig") as archivo:
                for linea in archivo:
                    try:
                        documento = json.loads(linea)
                        if not validar(documento):
                            raise ValueError("Documento inválido")
                        originales[huella(documento)] += 1
                    except (ValueError, TypeError):
                        invalidos += 1
            presentes = Counter(huella(documento) for documento in coleccion.find({}))
            faltantes = sum((originales - presentes).values())
            print(f"Dataset válidos: {sum(originales.values())} | Inválidos: {invalidos} | Originales faltantes: {faltantes}")
            comprobaciones["dataset_50000_validos"] = sum(originales.values()) == 50000 and invalidos == 0
            comprobaciones["originales_conservados"] = faltantes == 0
        print("Resumen de validación:")
        for nombre, resultado in comprobaciones.items():
            print(f"{nombre}: {'CORRECTO' if resultado else 'FALLO'}")
        return 0 if all(comprobaciones.values()) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PyMongoError, OSError, ValueError) as error:
        raise SystemExit(f"Verificación fallida: {error}")
