from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
import os
import random
import string
import subprocess
import json

app = FastAPI()

def is_supported_language(filename):
    # Add your supported languages here (Vyper)
    supported_languages = [".vy"]
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in supported_languages

def compile_files(task_id, files, vyper_version):
    # Your Vyper compilation logic here
    # This is just a dummy example that prints the filenames and Vyper version
    print(f"Task ID: {task_id}")
    print("Files to compile:")
    for file in files:
        print(file)
    print(f"Vyper version: {vyper_version}")

    # Replace this with actual Vyper compilation command using subprocess
    # Example command: subprocess.run(["vyper", "--version"]) or subprocess.run(["vyper", "my_contract.vy"])
    # Use vyper_version to specify the desired Vyper version in the command

@app.post("/compile/")
async def create_compilation_task(
    files: List[UploadFile] = File(...),
    vyper_version: str = Query(..., title="Vyper version to use for compilation")
):
    supported_files = [file.filename for file in files if is_supported_language(file.filename)]
    if not supported_files:
        raise HTTPException(status_code=400, detail="Unsupported file format or language")

    # Generate a task ID (for demonstration purposes, you can use a more robust method in a real application)
    task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Run the compilation task in the background using TaskIQ
    task_queue.add_task(compile_files, task_id, supported_files, vyper_version)

    return {"task_id": task_id}


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    # Check the status of the task (dummy example, replace with actual status tracking)
    # You should maintain the task status in a database or some other persistent storage
    # Here, we just return random statuses for illustration purposes
    statuses = ["In Progress", "Success", "Error"]
    return random.choice(statuses)

@app.get("/exceptions/{task_id}")
async def get_task_exceptions(task_id: str):
    # Fetch the exception information for a particular compilation task
    # This is just a dummy example, you should handle exceptions and errors appropriately
    status = await get_task_status(task_id)
    if status != "Error":
        raise HTTPException(status_code=400, detail="Task is not completed with Error status")
    
    # Dummy list of compilation errors (replace with actual errors)
    compilation_errors = ["Error 1: Compilation failed", "Error 2: Syntax error"]
    return {"task_id": task_id, "compilation_errors": compilation_errors}

@app.get("/compiled_artifact/{task_id}")
async def get_compiled_artifact(task_id: str):
    # Fetch the compiled artifact data in ethPM v3 format for a particular task
    # This is just a dummy example, you should handle the response data accordingly based on the actual compilation result
    status = await get_task_status(task_id)
    if status != "Success":
        raise HTTPException(status_code=400, detail="Task is not completed with Success status")

    # Dummy ethPM v3 formatted manifest (replace with actual compiled data)
    ethpm_manifest = {
        "contract_name": "MyContract",
        "abi": [{"name": "myFunction", "inputs": [], "outputs": []}],
        "compiler": {
            "name": "vyper",
            "version": "0.2.10",  # Replace with the actual Vyper compiler version used
            "settings": {}
        }
    }
    return json.dumps(ethpm_manifest)
