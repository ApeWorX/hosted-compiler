from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from ape import config
from ape_vyper.exceptions import VyperCompileError, VyperInstallError
from ethpm_types import PackageManifest
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, UploadFile
from pydantic import BaseModel

PackageManifest.update_forward_refs()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # NOTE: When running remix in local dev, this is the URL
        "http://localhost:8080",
        # NOTE: When running `npm run build && npm run preview`, this is the URL
        "http://localhost:4173",
        # NOTE: This is where the UI gets hosted
        "https://remix.ethereum.org",
        "https://remix-alpha.ethereum.org",
        "https://remix-beta.ethereum.org",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Task(BaseModel):
    id: str
    status: TaskStatus = TaskStatus.PENDING
    exceptions: List[str] = []
    manifest: Optional[PackageManifest] = None


# global db
results = {}
tasks: Dict[str, TaskStatus] = {}


def is_supported_language(filename):
    """
    Checks if the file is a vyper file.
    """
    # Add your supported languages here (Vyper)
    supported_languages = [".vy"]
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in supported_languages


@app.post("/compile/")
async def create_compilation_task(
    background_tasks: BackgroundTasks,
    files: List[UploadFile],
    vyper_version: str = Query(..., title="Vyper version to use for compilation"),
):
    """
    Creates the task with the list of vyper contracts.
    Compile and sets each file with a task.
    """
    project_root = Path(tempfile.mkdtemp(""))

    # Create a contracts directory
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir()

    # add request contracts in temp directory
    for file in files:
        content = await file.read()
        (project_root / "contracts" / file.filename).write_bytes(content)

    config_override = dict()
    if vyper_version:
        config_override["vyper"] = dict(version=vyper_version)

    tasks[project_root.name] = TaskStatus.PENDING
    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_project, project_root, config_override)

    return project_root.name


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """
    Check the status of each task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    return tasks[task_id]


@app.get("/exceptions/{task_id}")
async def get_task_exceptions(task_id: str) -> List[str]:
    """
    Fetch the exception information for a particular compilation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[task_id] is not TaskStatus.FAILED:
        raise HTTPException(
            status_code=400, detail="Task is not completed with Error status"
        )
    return results[task_id]


@app.get("/compiled_artifact/{task_id}")
async def get_compiled_artifact(task_id: str) -> Dict:
    """
    Fetch the compiled artifact data in ethPM v3 format for a particular task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[task_id] is not TaskStatus.SUCCESS:
        raise HTTPException(
            status_code=404, detail="Task is not completed with Success status"
        )
    # TODO Debug why it is producing serialize_response raise ResponseValidationError( fastapi.exceptions.ResponseValidationError ) when you use return results[task_id] as a PackageManifest
    return results[task_id].dict()


async def compile_project(project_root: Path, config_override: dict):
    """
    Compile the contract and assign the taskid to it
    """
    (project_root / "ape-config.yaml").unlink(missing_ok=True)
    (project_root / "ape-config.yaml").write_text(yaml.safe_dump(config_override))

    with config.using_project(project_root) as project:
        # TODO Handle and add more Error Types to except
        """
        Suggestion to make it easier to read:

        except (VyperInstallError, VyperCompileError):
            results[project_root.name] = [str(e)]
            tasks[project_root.name] = TaskStatus.FAILED
        """
        # compile contracts in folder wholesale
        try:
            project.load_contracts(use_cache=False)
            results[project_root.name] = project.extract_manifest()
            tasks[project_root.name] = TaskStatus.SUCCESS
        except VyperInstallError as e:
            results[project_root.name] = [str(e)]
            tasks[project_root.name] = TaskStatus.FAILED
        except VyperCompileError as e:
            results[project_root.name] = [str(e)]
            tasks[project_root.name] = TaskStatus.FAILED
