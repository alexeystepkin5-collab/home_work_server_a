from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Response, Query
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI(title="Todo API (simple)")

# In-memory хранилище
#Запись TASKS: Dict[int, dict] = {} в Python означает создание пустой переменной-словаря TASKS,
# инициализируемой как {}, с явным указанием типов данных (type hinting) для ключей и значений.
TASKS: Dict[int, dict] = {} #Аннотация типов (из модуля typing).
NEXT_ID = 1

# проверка наличия файла tasks.txt
file_path = Path("tasks.txt")
if file_path.is_file():  # Проверяет, что это файл, а не папка
    #print("Файл существует")
    with open('tasks.txt', 'r', encoding='utf-8') as file:
        TASKS = json.load(file)  # Читает весь файл восстанавливает json
        max_item = max(TASKS["tasks"], key=lambda x: x['id'])  # находим последнюю запись
        NEXT_ID = max_item['id'] + 1
else:
    print("Файл не найден")


# команда для запуска червера
# uvicorn main:app --reload --host 127.0.0.1 --port 8080

class Task(BaseModel):
    id: int
    title: str
    priopirty: str # я добавил приоритет
    isDone: bool


# GET /tasks -> список всех дел

# POST /tasks {"title": "Моя задача"}
class CreateTaskBody(BaseModel):
    title: str
    priority: str # я добавил приоритет

class CompleteTaskBody(BaseModel): #отметка о выполнении
    #task_id: Optional[int] = None
    #title: Optional[str] = None
    #priority: Optional[str] = None  # я добавил приоритет
    isDone: Optional[bool] = None

# PATCH /tasks/{id} {"title": "Моя Супер Задача"}
class PatchTaskBody(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None # я добавил приоритет
    isDone: Optional[bool] = None

# запрос корневого значения
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/tasks")
def list_tasks(
    q: Optional[str] = Query(default=None, description="search in title"),
    priority: Optional[str] = Query(default=None, description="search in priority"),
    isDone: Optional[bool] = Query(default=None, description="filter by isDone=true/false"),
):
    tasks = list(TASKS.values())

    if q:
        q_low = q.lower()
        tasks = [t for t in tasks if q_low in t["title"].lower()]

    if priority:
        priority_low = priority.lower()
        tasks = [t for t in tasks if priority_low in t["priority"].lower()]

    if isDone is not None:
        tasks = [t for t in tasks if t["isDone"] == isDone]

    return {"tasks": tasks}

#Создание задачи. Отправляется POST-запрос на сервер по пути /tasks с телом
# в виде JSON с полями title и priority. Сервер должен создать и сохранить задачу,
# выставить isDone в False, выдать задаче уникальный ID и в ответ отправить JSON
# со всеми четырьмя полями.

@app.post("/tasks", status_code=201)
def create_task(body: CreateTaskBody):
    global NEXT_ID

    title = body.title.strip()
    if not title:
        # для обучения можно показать, что валидация бывает на уровне API
        raise HTTPException(status_code=400, detail="title is required")

    priority = body.priority.strip() # я добавил приоритет
    if not priority:
        # для обучения можно показать, что валидация бывает на уровне API
        raise HTTPException(status_code=400, detail="priority is required")

    task = {"id": NEXT_ID, "title": title, "priority": priority, "isDone": False}
    TASKS[NEXT_ID] = task
    NEXT_ID += 1

    return {"task": task}

# отметка о выполнении
# 127.0.0.1:8080/tasks/1 #id=1 тело { "isDone": true }
@app.post("/tasks/{task_id}/complete", status_code=200)
def complete_task(task_id: int, body: CompleteTaskBody):

    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Not found")

    #if body.title is not None:
    #    title = body.title.strip()
    #    if not title:
    #        raise HTTPException(status_code=400, detail="title must be non-empty string")
    #    task["title"] = title

    #if body.priority is not None:
    #    priority = body.priority.strip()
    #    if not priority:
    #        raise HTTPException(status_code=400, detail="priority must be non-empty string")
    #    task["priority"] = priority

    if body.isDone is not None:
        task["isDone"] = body.isDone
    else:
        task["isDone"] = True

    return {} #{"task": task}

###########################################################################################

# 127.0.0.1:8080/tasks/1 #id=1 тело { "isDone": true }
@app.patch("/tasks/{task_id}/complete")
def patch_task(task_id: int, body: PatchTaskBody):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Not found")

    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="title must be non-empty string")
        task["title"] = title

    if body.priority is not None:
        priority = body.priority.strip()
        if not priority:
            raise HTTPException(status_code=400, detail="priority must be non-empty string")
        task["priority"] = priority

    if body.isDone is not None:
        task["isDone"] = body.isDone
    else:
        task["isDone"] = True

    return {"task": task}

# 127.0.0.1:8080/tasks/4 #id=4
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Not found")
    del TASKS[task_id]
    return Response(status_code=204)
