import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    database_name: str = "listenbrainz_db"
    collection_name: str = "listens"


settings = Settings()
