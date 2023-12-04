from fastapi.testclient import TestClient
import os
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

def test_cors_allowed_origins():
    # Define a list of allowed origins based on the configuration in main.py    
    allowed_origins = [
        "http://localhost:8080",
        "http://localhost:4173",
        "https://remix.ethereum.org",
        "https://remix-alpha.ethereum.org",
        "https://remix-beta.ethereum.org",
        "https://deploy-preview-123--remixproject.netlify.app",
        "https://deploy-preview-3333--remixproject.netlify.app",        
        os.environ["VYPER_HOSTED_COMPILER_CORS_ALLOWED_ORIGINS"] = ["test-from-env-var"],
    ]

    for origin in allowed_origins:
        response = client.options("/docs", headers={"Origin": origin})
        assert response.status_code == 200, f"Failed for origin: {origin}"

        # Check if the response contains the appropriate CORS headers
        assert response.headers.get("access-control-allow-origin") == origin, f"Failed for origin: {origin}"

    # Test an invalid origin and make sure it is not allowed
    invalid_origin = "https://invalid-origin.com"
    response = client.options("/docs", headers={"Origin": invalid_origin})
    assert response.status_code != 200, "Invalid origin should not be allowed"

    # Check if the response does not contain the CORS headers for the invalid origin
    assert "access-control-allow-origin" not in response.headers, "Invalid origin should not be in CORS headers"



