import argparse

from bson import json_util

from app.config import settings
from app.database import create_client


def build_pipelines():
    return {
        "unique_users": [{"$group": {"_id": "$user_name"}}, {"$count": "count"}],
        "unique_artists": [{"$group": {"_id": "$track_metadata.artist_name"}}, {"$count": "count"}],
        "top_artists": [
            {"$group": {"_id": "$track_metadata.artist_name", "listen_count": {"$sum": 1}}},
            {"$sort": {"listen_count": -1, "_id": 1}}, {"$limit": 5},
        ],
        "top_tracks": [
            {"$group": {"_id": {"artist_name": "$track_metadata.artist_name",
                                  "track_name": "$track_metadata.track_name"}, "listen_count": {"$sum": 1}}},
            {"$sort": {"listen_count": -1, "_id.artist_name": 1, "_id.track_name": 1}}, {"$limit": 10},
        ],
        "top_users": [
            {"$group": {"_id": "$user_name", "listen_count": {"$sum": 1}}},
            {"$sort": {"listen_count": -1, "_id": 1}}, {"$limit": 5},
        ],
        "average_duration": [
            {"$match": {"track_metadata.additional_info.duration_ms": {"$type": "number", "$gt": 0}}},
            {"$group": {"_id": None, "average_ms": {"$avg": "$track_metadata.additional_info.duration_ms"},
                         "samples": {"$sum": 1}}},
            {"$project": {"_id": 0, "average_ms": 1, "samples": 1,
                            "average_seconds": {"$divide": ["$average_ms", 1000]}}},
        ],
        "listens_by_day": [
            {"$match": {"timestamp": {"$type": "number", "$gte": 0, "$lte": 253402300799}}},
            {"$project": {"day": {"$dateToString": {"format": "%Y-%m-%d", "timezone": "UTC",
                          "date": {"$toDate": {"$multiply": ["$timestamp", 1000]}}}}}},
            {"$group": {"_id": "$day", "listen_count": {"$sum": 1}}}, {"$sort": {"_id": 1}},
        ],
    }


def run_queries(collection, artist_name):
    query = {"es_prueba": {"$ne": True}}
    print(json_util.dumps({"total_listens": collection.count_documents(query)}))
    for name, pipeline in build_pipelines().items():
        print(name)
        for result in collection.aggregate([{"$match": query}, *pipeline], allowDiskUse=True):
            print(json_util.dumps(result))
    for name, filters in [("recent_listens", query),
                          ("artist_listens", {**query, "track_metadata.artist_name": artist_name})]:
        print(name)
        for result in collection.find(filters, {"user_name": 1, "timestamp": 1, "track_metadata": 1}).sort(
            [("timestamp", -1), ("_id", -1)]
        ).limit(10):
            print(json_util.dumps(result))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist-name", default="NF & Sasha Sloan")
    args = parser.parse_args()
    with create_client() as client:
        run_queries(client[settings.database_name][settings.collection_name], args.artist_name)


if __name__ == "__main__":
    main()
