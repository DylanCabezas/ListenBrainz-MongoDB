from test_api import client, collection, payload


def test_partial_metadata_update(client):
    document = payload()
    document["track_metadata"]["additional_info"] = {"duration_ms": 1000, "source": "test"}
    identifier = client.post("/listens", json=document).json()["id"]
    response = client.patch(f"/listens/{identifier}", json={
        "track_metadata": {"track_name": "Updated", "additional_info": {"duration_ms": 2000}}
    })
    assert response.status_code == 200
    metadata = response.json()["track_metadata"]
    assert metadata["track_name"] == "Updated"
    assert metadata["artist_name"] == "Test artist"
    assert metadata["additional_info"] == {"duration_ms": 2000, "source": "test"}


def test_full_replacement(client):
    identifier = client.post("/listens", json=payload()).json()["id"]
    response = client.put(f"/listens/{identifier}", json=payload("replacement_user"))
    assert response.status_code == 200
    assert response.json()["id"] == identifier
    assert response.json()["user_name"] == "replacement_user"
    assert client.put("/listens/000000000000000000000000", json=payload()).status_code == 404


def test_unsafe_metadata_keys(client):
    identifier = client.post("/listens", json=payload()).json()["id"]
    for changes in [{"artist_name": None}, {"additional_info": {"$set": "unsafe"}},
                    {"artist_name.invalid": "unsafe"}, {}]:
        assert client.patch(f"/listens/{identifier}", json={"track_metadata": changes}).status_code == 422


def test_cursor_pages_with_mixed_identifiers(client, collection):
    created = [client.post('/listens', json=payload()).json()['id'] for _ in range(2)]
    collection.insert_one({**payload(), '_id': 'listenbrainz:legacy:1'})
    cursor = None
    found = []
    for _ in range(3):
        params = {'limit': 1}
        if cursor:
            params['cursor'] = cursor
        response = client.get('/listens/feed', params=params)
        assert response.status_code == 200
        found.extend(item['id'] for item in response.json()['items'])
        cursor = response.json()['next_cursor']
    assert cursor is None
    assert set(found) == {*created, 'listenbrainz:legacy:1'}
    assert len(found) == 3
    assert client.get('/listens/feed?cursor=invalid').status_code == 400
