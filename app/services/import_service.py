import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from pymongo.errors import BulkWriteError

from app.models import ListenCreate


def fingerprint(document):
    content = {key: value for key, value in document.items() if key != "_id"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validate_document(document):
    if not isinstance(document, dict) or "_id" in document:
        return False
    try:
        ListenCreate.model_validate({key: value for key, value in document.items() if key in ListenCreate.model_fields})
        return True
    except ValueError:
        return False


def insert_batch(collection, batch):
    if not batch:
        return 0
    try:
        return len(collection.insert_many(batch, ordered=False).inserted_ids)
    except BulkWriteError as error:
        if error.details.get("writeConcernErrors") or any(item["code"] != 11000 for item in error.details.get("writeErrors", [])):
            raise
        return error.details["nInserted"]


def import_file(collection, source, state_path, limit=1000, batch_size=1000, target=4000000, dry_run=True, progress=False):
    state_path = Path(state_path).resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_path.with_suffix(".lock.sqlite3")
    if Path(source).resolve() in (state_path, lock_path, state_path.with_suffix(".errors.jsonl")):
        raise ValueError("Source must differ from state and log paths")
    with closing(sqlite3.connect(lock_path, timeout=1)) as lock:
        lock.execute("BEGIN EXCLUSIVE")
        return process_file(collection, source, state_path, limit, batch_size, target, dry_run, progress)


def process_file(collection, source, state_path, limit=1000, batch_size=1000, target=4000000, dry_run=True, progress=False):
    if limit < 1 or not 1 <= batch_size <= 5000 or not 1 <= target <= 4000000:
        raise ValueError("Invalid import limits")
    started = time.monotonic()
    source = Path(source).resolve()
    state_path = Path(state_path).resolve()
    if source == state_path:
        raise ValueError("State path must differ from source")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    identity = f"{source}:{source.stat().st_size}:{source.stat().st_mtime_ns}"
    result = {"processed": 0, "inserted": 0, "duplicates": 0, "invalid": 0, "dry_run": dry_run}
    with sqlite3.connect(state_path, timeout=1) as state:
        state.execute("CREATE TABLE IF NOT EXISTS fingerprints (hash TEXT PRIMARY KEY)")
        state.execute("CREATE TABLE IF NOT EXISTS checkpoints (source TEXT PRIMARY KEY, offset INTEGER NOT NULL)")
        state.commit()
        state.execute("BEGIN IMMEDIATE")
        for document in collection.find({}).batch_size(batch_size):
            state.execute("INSERT OR IGNORE INTO fingerprints VALUES (?)", (fingerprint(document),))
        state.commit()
        checkpoint = state.execute("SELECT offset FROM checkpoints WHERE source = ?", (identity,)).fetchone()
        offset = checkpoint[0] if checkpoint and not dry_run else 0
        total = collection.count_documents({})
        result["initial_total"] = total
        result["source"] = str(source)
        result["offset"] = offset
        exhausted = False
        with source.open("rb") as stream, state_path.with_suffix(".errors.jsonl").open("a", encoding="utf-8") as errors:
            stream.seek(offset)
            while result["processed"] < limit and total < target:
                batch = []
                hashes = set()
                for _ in range(min(batch_size, limit - result["processed"], target - total)):
                    position = stream.tell()
                    line = stream.readline()
                    if not line:
                        exhausted = True
                        break
                    result["processed"] += 1
                    try:
                        document = json.loads(line.decode("utf-8-sig"))
                        if not validate_document(document):
                            raise ValueError("Invalid listen schema")
                        signature = fingerprint(document)
                    except (ValueError, TypeError, UnicodeError) as error:
                        result["invalid"] += 1
                        errors.write(json.dumps({"source": str(source), "offset": position, "error": str(error)}) + "\n")
                        errors.flush()
                        continue
                    if signature in hashes or state.execute("SELECT 1 FROM fingerprints WHERE hash = ?", (signature,)).fetchone():
                        result["duplicates"] += 1
                        continue
                    hashes.add(signature)
                    document["_id"] = f"listenbrainz:{signature}:1"
                    batch.append(document)
                if not dry_run:
                    inserted = insert_batch(collection, batch)
                    total += inserted
                    result["inserted"] += inserted
                    state.executemany("INSERT OR IGNORE INTO fingerprints VALUES (?)", [(value,) for value in hashes])
                    state.execute("INSERT OR REPLACE INTO checkpoints VALUES (?, ?)", (identity, stream.tell()))
                    state.commit()
                else:
                    state.executemany("INSERT OR IGNORE INTO fingerprints VALUES (?)", [(value,) for value in hashes])
                result["offset"] = stream.tell()
                if progress and result["processed"] % 10000 < batch_size:
                    print(json.dumps({**result, "total": total,
                                      "elapsed_seconds": round(time.monotonic() - started, 2)}), flush=True)
                if not line:
                    break
        result["total"] = total
        result["target_reached"] = total >= target
        result["source_exhausted"] = exhausted
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        result["candidates"] = result["processed"] - result["invalid"] - result["duplicates"]
        if dry_run:
            state.rollback()
        return result
