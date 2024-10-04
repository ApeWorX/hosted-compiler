from ethpm_types import PackageManifest

def test_create_compilation_task(client):
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


def test_get_task_status(client):
    # Test get task status
    response = client.get("/status/some_invalid_task_id")
    assert response.status_code == 404  # Not found

    task_id = client.post("/compile", json={"manifest": "ethpm/3"}).json()
    response = client.get(f"/status/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data.lower() in ["in progress", "success", "error"]


def test_get_task_exceptions(client):
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


def test_get_compiled_artifact(client):
    # Test get compiled artifact
    response = client.get("/artifacts/some_invalid_task_id")
    assert response.status_code == 404  # Not found

    # Assuming the task_id has a Success status
    source_id = "contracts/ERC20.vy"
    source_text = (Path(__file__).parent / source_id).read_text()
    manifest = {"manifest": "ethpm/3", "sources": {source_id: source_text}}
    task_id = client.post("/compile", json=manifest).json()
    response = client.get(f"/artifacts/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert "contract_name" in data
    assert "abi" in data
    assert "compiler" in data
    
def test_contract(client, manifest, file_to_compile):
    
    response = client.post("/compile", json=manifest.model_dump())
    assert response.status_code == 200
    task_id = response.json()
    
    response = client.get(f"status/{task_id}")
    assert response.status_code == 200
    
    task_status = response.json()
    
    if file_to_compile.name.startswith("fail") and task_status == "FAILED":
        assert client.get(f"/artifacts/{task_id}").status_code == 400
        response = client.get(f"/exceptions/{task_id}")
        assert response.status_code == 200
        assert len(response.json()) > 0
        
    elif file_to_compile.name.startswith("pass") and task_status == "SUCCESS":
        assert client.get(f"/exceptions/{task_id}").status_code == 400
        response = client.get(f"/artifacts/{task_id}")
        assert response.status_code == 200
        compiled_manifest = PackageManifest.model_validate(response.json())
        assert file_to_compile.stem in compiled_manifest.contract_types
        
    else:
        assert task_status != "PENDING"
