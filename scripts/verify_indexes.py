import json

from app.config import settings
from app.database import create_client, ensure_indexes


def main():
    with create_client() as client:
        collection = client[settings.database_name][settings.collection_name]
        ensure_indexes(collection)
        sample = collection.find_one({})
        if sample is None:
            raise SystemExit("No documents available to verify query plans")
        recent = collection.find_one({}, sort=[("timestamp", -1), ("_id", -1)])
        cursor_query = {"$or": [
            {"timestamp": {"$lt": recent["timestamp"]}},
            {"timestamp": recent["timestamp"], "$expr": {"$lt": ["$_id", {"$literal": recent["_id"]}]}}
        ]}
        for query in [{}, {"user_name": sample["user_name"]},
                      {"track_metadata.artist_name": sample["track_metadata"]["artist_name"]}, cursor_query]:
            plan = collection.database.command("explain", {
                "find": collection.name, "filter": query,
                "sort": {"timestamp": -1, "_id": -1}, "limit": 20,
            }, verbosity="executionStats")
            winning = json.dumps(plan["queryPlanner"]["winningPlan"])
            statistics = plan["executionStats"]
            result = {"filter": query, "uses_index": "IXSCAN" in winning,
                      "n_returned": statistics["nReturned"],
                      "keys_examined": statistics["totalKeysExamined"],
                      "documents_examined": statistics["totalDocsExamined"],
                      "execution_time_ms": statistics["executionTimeMillis"],
                      "winning_plan": plan["queryPlanner"]["winningPlan"]}
            print(json.dumps(result, default=str))
            if not result["uses_index"]:
                raise SystemExit("Query did not use IXSCAN")


if __name__ == "__main__":
    main()
