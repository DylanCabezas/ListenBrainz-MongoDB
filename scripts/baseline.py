from bson import json_util

from app.config import settings
from app.database import create_client


def main():
    with create_client() as client:
        collection = client[settings.database_name][settings.collection_name]
        print(json_util.dumps({"count": collection.count_documents({}),
                               "sample": collection.find_one({}, {"_id": 1})}))


if __name__ == "__main__":
    main()
