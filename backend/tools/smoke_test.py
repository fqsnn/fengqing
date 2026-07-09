import logging

from fastapi.testclient import TestClient

from app.main import app


def main() -> int:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    client = TestClient(app)
    for path in ("/", "/health", "/api/v1/status"):
        response = client.get(path)
        if response.status_code != 200:
            print(f"smoke failed: {path} -> {response.status_code}")
            return 1
    print("smoke=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
