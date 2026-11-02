import json

import mongomock
import pytest

from app.services.import_service import import_file


def record(number):
    return {"user_name": "import_user", "timestamp": number,
            "track_metadata": {"track_name": "Song", "artist_name": "Artist"}}


def test_stream_resume_duplicates_and_originals(tmp_path):
    collection = mongomock.MongoClient().db.listens
    original = record(1)
    collection.insert_one(original.copy())
    source = tmp_path / "source.listens"
    source.write_text("\n".join([json.dumps(record(1)), json.dumps(record(2)), "bad", json.dumps(record(3))]), encoding="utf-8")
    state = tmp_path / "state.sqlite3"
    assert import_file(collection, source, state, dry_run=True)["inserted"] == 0
    assert collection.count_documents({}) == 1
    first = import_file(collection, source, state, limit=2, batch_size=1, dry_run=False)
    assert first["inserted"] == 1
    second = import_file(collection, source, state, batch_size=1, dry_run=False)
    assert second["inserted"] == 1
    assert second["invalid"] == 1
    assert import_file(collection, source, state, dry_run=False)["inserted"] == 0
    assert collection.count_documents({}) == 3
    assert collection.find_one({"timestamp": 1})["track_metadata"] == original["track_metadata"]


def test_dry_run_duplicates_between_batches(tmp_path):
    collection = mongomock.MongoClient().db.listens
    source = tmp_path / "duplicates.jsonl"
    source.write_text("\n".join(json.dumps(record(1)) for _ in range(3)), encoding="utf-8")
    state = tmp_path / "state.sqlite3"
    result = import_file(collection, source, state, batch_size=1)
    assert result["duplicates"] == 2
    assert result["candidates"] == 1
    assert collection.count_documents({}) == 0
    assert import_file(collection, source, state, batch_size=1, dry_run=False)["inserted"] == 1


def test_target(tmp_path):
    collection = mongomock.MongoClient().db.listens
    source = tmp_path / "data.jsonl"
    source.write_text("\n".join(json.dumps(record(i)) for i in range(5)), encoding="utf-8")
    state = tmp_path / "state.sqlite3"
    assert import_file(collection, source, state, target=2, dry_run=False)["inserted"] == 2
    assert collection.count_documents({}) == 2
    assert import_file(collection, source, state, target=4, dry_run=False)["inserted"] == 2
    assert collection.count_documents({}) == 4


def test_recovery_after_partial_write(tmp_path, monkeypatch):
    from app.services import import_service
    from pymongo.errors import AutoReconnect

    collection = mongomock.MongoClient().db.listens
    source = tmp_path / "data.jsonl"
    source.write_text("\n".join(json.dumps(record(i)) for i in range(3)), encoding="utf-8")
    state = tmp_path / "state.sqlite3"
    original_insert = import_service.insert_batch

    def interrupted_insert(target_collection, batch):
        target_collection.insert_one(batch[0])
        raise AutoReconnect("Simulated interrupted acknowledgement")

    monkeypatch.setattr(import_service, "insert_batch", interrupted_insert)
    with pytest.raises(AutoReconnect):
        import_file(collection, source, state, dry_run=False)
    monkeypatch.setattr(import_service, "insert_batch", original_insert)
    assert import_file(collection, source, state, dry_run=False)["inserted"] == 2
    assert collection.count_documents({}) == 3
