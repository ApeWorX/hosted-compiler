import re
from pathlib import Path

from fastapi.testclient import TestClient
from main import app
import pytest

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
    task_id = response.json()
    assert isinstance(task_id, str)


def test_get_task_status():
    # Test get task status
    response = client.get("/status/some_invalid_task_id")
    assert response.status_code == 404  # Not found

    task_id = client.post("/compile", json={"manifest": "ethpm/3"}).json()
    response = client.get(f"/status/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data.lower() in ["in progress", "success", "error"]


def test_get_task_exceptions():
    # Test get task exceptions
    response = client.get("/exceptions/some_invalid_task_id")
    assert response.status_code == 404  # Not found

    # Assuming the task_id has an Error status
    task_id = client.post("/compile", json={"manifest": "ethpm/3"}).json()
    response = client.get(f"/exceptions/{task_id}")
    assert response.status_code == 400
    data = response.json()
    actual = data["detail"]
    assert re.match(r"Task '\w*' is not completed with Error status", actual)


def test_get_compiled_artifact():
    # Test get compiled artifact
    response = client.get("/artifacts/some_invalid_task_id")
    assert response.status_code == 404  # Not found

    # Assuming the task_id has a Success status
    source_id = "contracts/ERC20.vy"
    source_text = (Path(__file__).parent / source_id).read_text()
    manifest = {"manifest": "ethpm/3", "sources": {source_id: source_text}}
    task_id = client.post("/compile", json=manifest).json()
    response = client.get(f"/artifacts/{task_id}")
    data = response.json()

    if response.status_code == 404:
        # Bad request. Let's check for the exception.
        response = client.get(f"/exceptions/{task_id}")
        if response.status_code == 200:
            # This will show actual compiler errors in the tests.
            error_data = response.json()
            errors = "\n".join(error_data) if isinstance(error_data, list) else f"{error_data}"
            pytest.fail(errors)

    else:
        assert response.status_code == 200, data

    assert "name" in data
    assert "contractTypes" in data
    assert "compilers" in data

    # Show we get the ERC20 contract-type.
    assert "ERC20" in data["contractTypes"]
    assert "abi" in data["contractTypes"]["ERC20"]
    assert len(data["contractTypes"]["ERC20"]["abi"]) > 1
