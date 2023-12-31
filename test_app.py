from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_compilation_task():
    # Test create compilation task
    response = client.post("/compile")
    assert (
        response.status_code == 422
    )  # Since the manifest parameter is missing, it should return 422 Unprocessable Entity

    # empty sources should work
    response = client.post("/compile", json={"manifest": "ethpm/3"})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data


def test_get_task_status():
    # Test get task status
    response = client.get("/status/some_invalid_task_id")
    assert response.status_code == 400  # Invalid task_id should return 400 Bad Request

    response = client.get("/status/some_valid_task_id")
    assert response.status_code == 200
    data = response.json()
    assert data in ["In Progress", "Success", "Error"]


def test_get_task_exceptions():
    # Test get task exceptions
    response = client.get("/exceptions/some_invalid_task_id")
    assert response.status_code == 400  # Invalid task_id should return 400 Bad Request

    # Assuming the task_id has an Error status
    response = client.get("/exceptions/some_valid_task_id")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "compilation_errors" in data


def test_get_compiled_artifact():
    # Test get compiled artifact
    response = client.get("/artifacts/some_invalid_task_id")
    assert response.status_code == 400  # Invalid task_id should return 400 Bad Request

    # Assuming the task_id has a Success status
    response = client.get("/artifacts/some_valid_task_id")
    assert response.status_code == 200
    data = response.json()
    assert "contract_name" in data
    assert "abi" in data
    assert "compiler" in data
