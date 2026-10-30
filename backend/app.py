"""In-memory task API for the parallel-agent demo."""

from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictBool, field_validator

app = FastAPI(title="Todo demo")
tasks: dict[str, "Task"] = {}


class Task(BaseModel):
    id: str
    title: str
    completed: bool = False


class CreateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 120:
            raise ValueError("Title must contain 1 to 120 characters")
        return value


class UpdateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed: StrictBool


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": "Invalid task data"})


@app.get("/api/tasks")
def list_tasks() -> dict[str, list[Task]]:
    return {"tasks": list(tasks.values())}


@app.post("/api/tasks", status_code=201)
def create_task(payload: CreateTask) -> Task:
    task = Task(id=str(uuid4()), title=payload.title)
    tasks[task.id] = task
    return task


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: str, payload: UpdateTask) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = payload.completed
    return task
