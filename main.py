from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
import asyncio 
import os
import random
import string
from pydantic import BaseModel
from enum import Enum
from typing import Dict, Optional, List
from ethpm_types import PackageManifest

app = FastAPI()

class TaskStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Task(BaseModel):
    id: str
    status: TaskStatus = TaskStatus.PENDING
    exceptions: List[str] = []
    manifest : Optional[PackageManifest] = None

    
tasks: Dict[str,Task] = {}

def is_supported_language(filename):
    # Add your supported languages here (Vyper)
    supported_languages = [".vy"]
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in supported_languages

async def compile_files(task_id, files): #vyper_version):
    # Your Vyper compilation logic here
    # This is just a dummy example that prints the filenames and Vyper version
    tasks[task_id] = Task(id=task_id)
    print(f"Task ID: {task_id}")
    await asyncio.sleep(60)
    print("Files to compile:")
    for file in files:
        print(file)
    #print(f"Vyper version: {vyper_version}")
    tasks[task_id].status = random.choice([TaskStatus.FAILED, TaskStatus.SUCCESS])

    if tasks[task_id].status is TaskStatus.FAILED:
        tasks[task_id].exceptions = [
            str(Exception("Bad choice")),
            str(Exception("Wrenches")),
        ]
    else:
        tasks[task_id].manifest = PackageManifest()

@app.post("/compile/")
async def create_compilation_task(
    background_tasks: BackgroundTasks,
    files: List[UploadFile],
    # vyper_version: str = Query(..., title="Vyper version to use for compilation"),
):
    supported_files = [file.filename for file in files if is_supported_language(file.filename)]
    if not supported_files:
        raise HTTPException(status_code=400, detail="Unsupported file format or language")

    # Generate a task ID (for demonstration purposes, you can use a more robust method in a real application)
    task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_files, task_id, supported_files) #vyper_version)
    return {"task_id": task_id}


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    # Check the status of the task (dummy example, replace with actual status tracking)
    # You should maintain the task status in a database or some other persistent storage
    # Here, we just return random statuses for illustration purposes
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    return tasks[task_id].status

@app.get("/exceptions/{task_id}")
async def get_task_exceptions(task_id: str) -> List[str]:
    # Fetch the exception information for a particular compilation task
    # This is just a dummy example, you should handle exceptions and errors appropriately
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[id].status is not TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail="Task is not completed with Error status")
    return tasks[task_id].exceptions

@app.get("/compiled_artifact/{task_id}")
async def get_compiled_artifact(task_id: str) -> PackageManifest:
    # Fetch the compiled artifact data in ethPM v3 format for a particular task
    # This is just a dummy example, you should handle the response data accordingly based on the actual compilation result
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task id not found")
    if tasks[id].status is not TaskStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Task is not completed with Success status")
    return tasks[task_id].manifest
