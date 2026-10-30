"""Run against the Vite server on 127.0.0.1:5173 with the backend on 8000."""

import json
import urllib.error
import urllib.request
from uuid import uuid4

BASE = "http://127.0.0.1:5173/api/tasks"


def request(method, url, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.load(response)


def main():
    status, initial = request("GET", BASE)
    assert status == 200 and isinstance(initial["tasks"], list)
    title = "Integration smoke " + str(uuid4())
    status, created = request("POST", BASE, {"title": title})
    assert status == 201 and created["title"] == title and created["completed"] is False
    status, updated = request("PATCH", f"{BASE}/{created['id']}", {"completed": True})
    assert status == 200 and updated["id"] == created["id"] and updated["completed"] is True
    _, final = request("GET", BASE)
    assert any(t["id"] == created["id"] and t["completed"] for t in final["tasks"])
    print("PASS: frontend proxy → backend list, create, complete, and reload")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, KeyError, ValueError, urllib.error.URLError) as exc:
        raise SystemExit(f"FAIL: {exc}. Start both servers as described in README.md") from exc
