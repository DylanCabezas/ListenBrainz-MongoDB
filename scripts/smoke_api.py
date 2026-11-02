import json

from fastapi.testclient import TestClient

from app.main import create_app


def main():
    with TestClient(create_app()) as client:
        results = {}
        for path in ["/docs", "/openapi.json", "/listens?limit=1", "/listens/feed?limit=2", "/listens/stats/summary",
                     "/listens/stats/top-artists?limit=3"]:
            response = client.get(path)
            response.raise_for_status()
            results[path] = response.status_code
            if path == "/listens/stats/summary":
                results["summary"] = response.json()
        print(json.dumps(results))


if __name__ == "__main__":
    main()
