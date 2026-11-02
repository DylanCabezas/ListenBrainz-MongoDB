import os
from uuid import uuid4

import mongomock
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.main import create_app


@pytest.fixture
def collection():
    return mongomock.MongoClient().listenbrainz_test.listens


@pytest.fixture
def client(collection):
    with TestClient(create_app(collection)) as session:
        yield session


def payload(user="test_user"):
    return {"user_name": user, "timestamp": 1700000000,
            "track_metadata": {"track_name": "Test track", "artist_name": "Test artist"}}


def exercise_crud(client, user):
    identifiers = []
    try:
        for _ in range(2):
            created = client.post("/listens", json=payload(user))
            assert created.status_code == 201
            identifiers.append(created.json()["id"])
        for identifier in identifiers:
            assert client.get(f"/listens/{identifier}").json()["user_name"] == user
            updated = client.patch(f"/listens/{identifier}", json={"timestamp": 1700000001})
            assert updated.status_code == 200
            assert updated.json()["timestamp"] == 1700000001
            renamed = client.patch(f"/listens/{identifier}", json={
                "track_metadata": {"track_name": "Updated test track"}
            })
            assert renamed.status_code == 200
            assert renamed.json()["track_metadata"]["artist_name"] == "Test artist"
        replacement = client.put(f"/listens/{identifiers[0]}", json=payload(user))
        assert replacement.status_code == 200
        assert replacement.json()["id"] == identifiers[0]
        feed = client.get("/listens/feed", params={"user_name": user, "limit": 1})
        assert feed.status_code == 200
        assert feed.json()["next_cursor"]
        next_page = client.get("/listens/feed", params={
            "user_name": user, "limit": 1, "cursor": feed.json()["next_cursor"]
        })
        assert next_page.status_code == 200
        assert next_page.json()["items"][0]["id"] != feed.json()["items"][0]["id"]
        page = client.get("/listens", params={"user_name": user, "limit": 1, "page": 2})
        assert page.status_code == 200
        assert page.json()["total"] == 2
        assert len(page.json()["items"]) == 1
        for identifier in identifiers:
            assert client.delete(f"/listens/{identifier}").status_code == 204
            assert client.get(f"/listens/{identifier}").status_code == 404
    finally:
        for identifier in identifiers:
            client.delete(f"/listens/{identifier}")


def test_crud(client):
    exercise_crud(client, "test_user")


def test_validation(client):
    assert client.post("/listens", json={}).status_code == 422
    assert client.post("/listens", json={**payload(), "timestamp": True}).status_code == 422
    assert client.get("/listens/not-an-id").status_code == 400
    assert client.get("/listens/000000000000000000000000").status_code == 404
    assert client.get("/listens?limit=101").status_code == 422
    assert client.get("/listens?start_timestamp=2&end_timestamp=1").status_code == 400
    assert client.patch("/listens/000000000000000000000000", json={}).status_code == 422
    assert client.patch("/listens/000000000000000000000000", json={"timestamp": None}).status_code == 422


def test_filters_statistics_and_legacy_id(client, collection):
    collection.insert_one({**payload(), "_id": "listenbrainz:legacy:1"})
    assert client.get("/listens/listenbrainz:legacy:1").status_code == 200
    assert client.get("/listens?artist_name=Test%20artist&start_timestamp=1700000000").json()["total"] == 1
    assert client.get("/listens?end_timestamp=1").json()["total"] == 0
    assert client.get("/listens/stats/summary").json() == {"total_listens": 1, "unique_users": 1}
    assert client.get("/listens/stats/top-artists").json()[0]["listen_count"] == 1


@pytest.mark.skipif(os.getenv("RUN_MONGO_TESTS") != "1", reason="Explicit local MongoDB integration opt-in")
def test_local_mongo_crud():
    with MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"), serverSelectionTimeoutMS=5000) as mongo:
        collection = mongo.listenbrainz_db.listens
        before = collection.count_documents({})
        with TestClient(create_app(collection)) as client:
            exercise_crud(client, f"api_test_{uuid4().hex}")
        assert collection.count_documents({}) == before
