from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.database import SessionLocal
from ..models.task import Task
from ..schemas.task_schemas import TaskCreate, TaskUpdate, TaskBase

router = APIRouter()


# Подключение к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Эндпоинт для создания задачи
@router.post("/tasks/", response_model=dict)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(title=task.title, description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Задача успешно создана!", "task_id": new_task.id}


# Эндпоинт для получения всех задач
@router.get("/tasks/", response_model=list[dict])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "is_completed": t.is_completed,
            "created_at": t.created_at,
        }
        for t in tasks
    ]


# Эндпоинт для получения одной задачи по ID
@router.get("/tasks/{task_id}/", response_model=dict)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_completed": task.is_completed,
        "created_at": task.created_at,
    }


# Эндпоинт для обновления задачи по ID
@router.put("/tasks/{task_id}/", response_model=dict)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):  # Тут TaskUpdate!
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.is_completed is not None:
        task.is_completed = task_update.is_completed

    db.commit()
    db.refresh(task)

    return {
        "message": "Задача успешно обновлена",
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
            "created_at": task.created_at,
        },
    }


# Эндпоинт для удаления задачи (пока пустой — заполним позже)
@router.delete("/tasks/{task_id}/", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()

    return {"message": "Задача успешно удалена"}

