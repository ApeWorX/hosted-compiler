from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
import os
from pydantic import BaseModel
from enum import Enum
from typing import Dict, Optional, List
from ethpm_types import PackageManifest

import tempfile

import asyncio
from concurrent.futures import ThreadPoolExecutor

from ape import compilers, config
from pathlib import Path




PackageManifest.update_forward_refs()
app = FastAPI()


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
    Creates the task with the list of vyper contracts to compile 
    and sets each file with a task.
    """
    project_root = Path(tempfile.mkdtemp(""))

    # Create a contracts directory
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir()

    # add request contracts in temp directory
    for file in files:
        content = (await file.read()).decode("utf-8")
        (project_root / "contracts" / file.filename).write_text(content)

    tasks[project_root.name] = TaskStatus.PENDING
    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_project, project_root, files)

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
    if tasks[id].status is not TaskStatus.FAILED:
        raise HTTPException(
            status_code=400, detail="Task is not completed with Error status"
        )
    return tasks[task_id]


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


async def compile_project(project_root: Path, files: List[UploadFile]):
    """
    Compile the contrct and asssign the taskid to it
    """
    with config.using_project(project_root) as project:
        results[project_root.name] = project.extract_manifest()
    tasks[project_root.name] = TaskStatus.SUCCESS
