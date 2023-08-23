from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
import asyncio
import os
import random
import string
from pydantic import BaseModel
from enum import Enum
from typing import Dict, Optional, List
from ethpm_types import PackageManifest

import tempfile
import shutil
import vyper

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
    content = await files[0].read()
    project_root = Path(tempfile.mkdtemp(""))

    tasks[project_root.name] = TaskStatus.PENDING
    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_project, project_root, files)

    return project_root.name


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    # Check the status of the task (dummy example, replace with actual status tracking)
    # You should maintain the task status in a database or some other persistent storage
    # Here, we just return random statuses for illustration purposes
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    return tasks[task_id]


@app.get("/exceptions/{task_id}")
async def get_task_exceptions(task_id: str) -> List[str]:
    # Fetch the exception information for a particular compilation task
    # This is just a dummy example, you should handle exceptions and errors appropriately
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[id].status is not TaskStatus.FAILED:
        raise HTTPException(
            status_code=400, detail="Task is not completed with Error status"
        )
    return tasks[task_id]


@app.get("/compiled_artifact/{task_id}", response_model=PackageManifest)
async def get_compiled_artifact(task_id: str):
    # Fetch the compiled artifact data in ethPM v3 format for a particular task
    # This is just a dummy example, you should handle the response data accordingly based on the actual compilation result
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[task_id] is not TaskStatus.SUCCESS:
        raise HTTPException(
            status_code=404, detail="Task is not completed with Success status"
        )

    return results[task_id]


async def compile_project(project_root: Path, files: List[UploadFile]):
    # Create a contracts directory
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir()

    # add request contracts in temp directory
    # files[0].headers["content-disposition"].split("; ")[-1].split("=")[-1].strip('"')
    for file in files:
        filename = (
            file.headers["content-disposition"]
            .split("; ")[-1]
            .split("=")[-1]
            .strip('"')
        )
        content = await file.read()
        (project_root / "contracts" / filename).write_text(content.decode("utf-8"))

    # compile project
    with config.using_project(project_root) as project:
        results[project_root.name] = project.extract_manifest()

    tasks[project_root.name] = TaskStatus.SUCCESS
