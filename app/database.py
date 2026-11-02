from pymongo import MongoClient

from app.config import settings


def create_client():
    return MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)


def ensure_indexes(collection):
    for keys in [
        [("timestamp", -1), ("_id", -1)],
        [("user_name", 1), ("timestamp", -1), ("_id", -1)],
        [("track_metadata.artist_name", 1), ("timestamp", -1), ("_id", -1)],
    ]:
        collection.create_index(keys)
