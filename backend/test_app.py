import pytest
from fastapi.testclient import TestClient

from app import app, tasks


@pytest.fixture(autouse=True)
def clear_tasks():
    tasks.clear()
    yield
    tasks.clear()


def test_create_list_and_complete_task():
    client = TestClient(app)
    assert client.get("/api/tasks").json() == {"tasks": []}
    response = client.post("/api/tasks", json={"title": "  Buy milk  "})
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Buy milk"
    assert task["completed"] is False
    assert client.get("/api/tasks").json() == {"tasks": [task]}
    response = client.patch(f"/api/tasks/{task['id']}", json={"completed": True})
    assert response.status_code == 200
    assert response.json() == {**task, "completed": True}


@pytest.mark.parametrize("title", ["", "  ", "x" * 121])
def test_invalid_titles_return_contract_error(title):
    response = TestClient(app).post("/api/tasks", json={"title": title})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_unknown_task_and_invalid_completion():
    client = TestClient(app)
    assert client.patch("/api/tasks/missing", json={"completed": True}).status_code == 404
    response = client.patch("/api/tasks/missing", json={"completed": "yes"})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
