from  pathlib import Path
import pytest
from ethpm_types import PackageManifest, Source
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


ALL_FILES = {p.name: p for p in (Path(__file__).parent.parent/"contracts").glob("*.vy")}


@pytest.fixture(scope = "session" ,params=ALL_FILES)
def file_to_compile(request):
    
    return ALL_FILES[request.param]

@pytest.fixture(scope = "session")
def manifest(file_to_compile):
    
    return PackageManifest(sources= {file_to_compile.name: Source(content = file_to_compile.read_text())})

@pytest.fixture(scope = "session")
def client():
    return TestClient(app)
    





