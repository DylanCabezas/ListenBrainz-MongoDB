import argparse
import time
from uuid import uuid4

import httpx


def run_demo(base_url, rounds):
    with httpx.Client(base_url=base_url, timeout=30) as client:
        for number in range(rounds):
            identifier = None
            try:
                response = client.post("/listens", json={
                    "user_name": f"python_demo_{uuid4().hex}", "timestamp": int(time.time()),
                    "track_metadata": {"track_name": "Python demo", "artist_name": "Demo artist"},
                })
                response.raise_for_status()
                identifier = response.json()["id"]
                print(f"Round {number + 1}: CREATE {response.status_code} id={identifier}")
                response = client.get(f"/listens/{identifier}")
                response.raise_for_status()
                print(f"READ {response.status_code}")
                response = client.patch(f"/listens/{identifier}", json={
                    "track_metadata": {"track_name": "Updated Python demo", "artist_name": "Updated artist"},
                })
                response.raise_for_status()
                if response.json()["track_metadata"]["track_name"] != "Updated Python demo":
                    raise RuntimeError("Update verification failed")
                print(f"UPDATE {response.status_code}")
            finally:
                if identifier is not None:
                    response = client.delete(f"/listens/{identifier}")
                    response.raise_for_status()
                    print(f"DELETE {response.status_code}")
                    if client.get(f"/listens/{identifier}").status_code != 404:
                        raise RuntimeError("Delete verification failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 100:
        parser.error("--rounds must be between 1 and 100")
    run_demo(args.base_url, args.rounds)


if __name__ == "__main__":
    main()
