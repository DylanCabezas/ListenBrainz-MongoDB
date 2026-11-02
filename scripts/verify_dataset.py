import argparse
import json
from collections import Counter
from itertools import islice
from pathlib import Path

from bson import json_util

from app.config import settings
from app.database import create_client
from app.services.import_service import fingerprint, validate_document


def capture_baseline(collection, destination):
    if destination.exists():
        raise ValueError("Baseline already exists; it will not be overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        for document in collection.find({"_id": {"$type": "objectId"}}).batch_size(1000):
            stream.write(json_util.dumps({"_id": document["_id"], "fingerprint": fingerprint(document)}) + "\n")


def verify_dataset(collection, source, baseline):
    expected = Counter()
    invalid = 0
    with source.open(encoding="utf-8-sig") as stream:
        for line in stream:
            try:
                document = json.loads(line)
                if not validate_document(document):
                    raise ValueError("Invalid source document")
                expected[fingerprint(document)] += 1
            except (ValueError, TypeError):
                invalid += 1
    preserved = Counter()
    changed = missing = checked = 0
    with baseline.open(encoding="utf-8") as stream:
        while batch := list(islice(stream, 1000)):
            records = [json_util.loads(line) for line in batch]
            documents = {document["_id"]: document for document in collection.find(
                {"_id": {"$in": [record["_id"] for record in records]}}
            )}
            for record in records:
                checked += 1
                document = documents.get(record["_id"])
                if document is None:
                    missing += 1
                elif fingerprint(document) != record["fingerprint"]:
                    changed += 1
                else:
                    preserved[record["fingerprint"]] += 1
    result = {"total_listens": collection.count_documents({}), "baseline_checked": checked,
              "baseline_missing": missing, "baseline_changed": changed, "source_invalid": invalid,
              "source_valid": sum(expected.values()), "source_originals_missing": sum((expected - preserved).values())}
    print(json.dumps(result), flush=True)
    if missing or changed or invalid or result["source_originals_missing"] or result["source_valid"] != 50000:
        raise RuntimeError("Original dataset verification failed")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=Path("data/original_baseline.jsonl"))
    parser.add_argument("--capture-baseline", action="store_true")
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    sources = list(Path("data").rglob("listenbrainz_50000.jsonl")) if args.source is None else [args.source]
    if len(sources) != 1:
        parser.error("Specify a unique original 50000-document source")
    with create_client() as client:
        collection = client[settings.database_name][settings.collection_name]
        if args.capture_baseline:
            capture_baseline(collection, args.baseline)
        verify_dataset(collection, sources[0], args.baseline)


if __name__ == "__main__":
    main()
