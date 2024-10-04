import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Annotated

from ape import Project
from ape.managers.compilers import CompilerError
from ethpm_types import PackageManifest
from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import re

class CompilerErrorResponse(BaseModel):
    status: str = "failed"
    message: str
    column: int | None = None
    line: int | None = None
    error_type: str

def init_openapi(app: FastAPI):
    # https://github.com/tiangolo/fastapi/discussions/10524
    # Copied from FastAPI, and customized the version
    async def swagger_ui_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
        if oauth2_redirect_url:
            oauth2_redirect_url = root_path + oauth2_redirect_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=oauth2_redirect_url,
            init_oauth=app.swagger_ui_init_oauth,
            swagger_ui_parameters=app.swagger_ui_parameters,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        )

    app.add_route("/docs", swagger_ui_html, include_in_schema=False)

    if app.swagger_ui_oauth2_redirect_url:

        async def swagger_ui_redirect(req: Request) -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()

        app.add_route(
            app.swagger_ui_oauth2_redirect_url,
            swagger_ui_redirect,
            include_in_schema=False,
        )


app = FastAPI(
    docs_url=None,  # https://github.com/tiangolo/fastapi/discussions/10524
)
init_openapi(app)

PackageManifest.model_rebuild()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    exceptions: list[str] = []
    manifest: PackageManifest | None = None


# global db
results: dict[str, PackageManifest | list[str]] = {}
tasks: dict[str, TaskStatus] = {}


def is_supported_language(filename) -> bool:
    """
    Checks if the file is a vyper file.
    """
    # Add your supported languages here (Vyper)
    supported_languages = [".vy"]
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in supported_languages

@app.post("/compile")
async def new_compilation_task(
    background_tasks: BackgroundTasks,
    project: Annotated[PackageManifest, Body()],
) -> str:
    """
    Creates a compilation task using the given project encoded as an EthPM v3 manifest.
    """
    project_root = Path(tempfile.mkdtemp(""))

    task_id = project_root.name
    tasks[task_id] = TaskStatus.PENDING
    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_project, project_root, project)

    return task_id


@app.put("/compile/{task_id}")
async def updated_compilation_task(
    background_tasks: BackgroundTasks,
    task_id: str,
    project: Annotated[PackageManifest, Body()],
) -> str:
    """
    Re-triggers a compilation task using the updated project encoded as an EthPM v3 manifest.
    """
    project_root = Path(f"{tempfile.gettempdir()}/{task_id}")
    if not project_root.exists():
        raise HTTPException(status_code=404, detail=f"task ID '{task_id}' not found")

    tasks[task_id] = TaskStatus.PENDING
    # Run the compilation task in the background using TaskIQ
    background_tasks.add_task(compile_project, project_root, project)

    return task_id


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """
    Check the status of each task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"task ID '{task_id}' not found")
    return tasks[task_id]


@app.get("/exceptions/{task_id}")
async def get_task_exceptions(task_id: str) -> list[CompilerErrorResponse]:
    """
    Fetch the exception information for a particular compilation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"task ID '{task_id}' not found")
    
    if tasks[task_id] is not TaskStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is not completed with Error status",
        )
    return results[task_id]


# NOTE: `response_model=None` so that we only use our own validation
#   from ethpm_types.
@app.get("/artifacts/{task_id}", response_model=None)
async def get_compiled_artifact(task_id: str) -> dict:
    """
    Fetch the compiled artifact data in ethPM v3 format for a particular task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"task ID '{task_id}' not found")
    if tasks[task_id] is not TaskStatus.SUCCESS:
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is not completed with Success status",
        )

    return results[task_id]

def extract_line_and_column(error_message: str) -> tuple[int, int]:
    # Regex to capture "line <line_number>:<column_number>"
    match = re.search(r'line (\d+):(\d+)', error_message)
    if match:
        line_number = int(match.group(1))  # First capture group is the line number
        column_number = int(match.group(2))  # Second capture group is the column number
        return line_number, column_number
    return 0, 0  # Default to 0 for both if no match is found

async def compile_project(project_root: Path, manifest: PackageManifest) -> None:
    """
    Compile the contract and assign the taskID to it
    """
    # Create a contracts directory
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir()
    project = Project.from_manifest(manifest)

    try:
        # NOTE: Updates itself because manifest projects are their own cache.
        project.load_contracts()
    except CompilerError as e:
        error_message = str(e)
        line, column = None, None
        
         # Regex pattern to find "line X:Y"
        match = re.search(r'line (\d+):(\d+)', error_message)
        if match:
            line = int(match.group(1))
            column = int(match.group(2))
        
        # Convert the error details into the Pydantic model
        error_details = [
            CompilerErrorResponse(
                message=str(e),
                line=line,
                column=column,
                error_type=e.__class__.__name__,
            )
            ]
        results[project_root.name] = error_details
        tasks[project_root.name] = TaskStatus.FAILED

    except Exception as e:
        # Handle any other exceptions that occur
        generic_error_response = CompilerErrorResponse(
            message=str(e),
            column=0,  # Default for general exceptions, since they might not have source locations
            line=0,    # Default for general exceptions
            error_type=e.__class__.__name__
        )
        
        results[project_root.name] = [generic_error_response]
        tasks[project_root.name] = TaskStatus.FAILED
    else:
        results[project_root.name] = manifest
        tasks[project_root.name] = TaskStatus.SUCCESS
