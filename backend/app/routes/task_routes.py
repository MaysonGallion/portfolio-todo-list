from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database.database import SessionLocal
from ..models.task import Task
from ..schemas.task_schemas import TaskCreate, TaskUpdate, TaskListResponse
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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
    logger.info(f"Получен запрос на создание задачи: {task.title}")
    new_task = Task(title=task.title, description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    logger.info(f"Задача создана успешно: id={new_task.id}, title={new_task.title}")
    return {"message": "Задача успешно создана!", "task_id": new_task.id}


# Эндпоинт для получения всех задач с фильтрами и пагинацией
@router.get("/tasks/", response_model=TaskListResponse)
def get_tasks(
        db: Session = Depends(get_db),
        is_completed: Optional[bool] = Query(None, description="Фильтр: true - выполненные, false - невыполненные"),
        q: Optional[str] = Query(None, min_length=2, description="Поиск по названию задачи (не менее 2 символов)"),
        page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
        size: int = Query(5, ge=1, le=100, description="Количество задач на странице (по умолчанию 5, макс. 100)")
):
    logger.info(f"Получен запрос на получение всех задач (страница {page}, размер {size})")

    query = db.query(Task)

    if is_completed is not None:
        logger.info(f"Фильтр по статусу: {is_completed}")
        query = query.filter(Task.is_completed == is_completed)

    if q:
        logger.info(f"Фильтр по названию: {q}")
        query = query.filter(Task.title.ilike(f"%{q}%"))

    total_tasks = query.with_entities(Task.id).count()  # Оптимизировано для скорости

    tasks = query.order_by(Task.created_at.desc()).offset((page - 1) * size).limit(size).all()

    logger.info(f"Найдено задач: {len(tasks)} из {total_tasks} (стр. {page})")
    return {
        "total": total_tasks,
        "page": page,
        "size": size,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "is_completed": t.is_completed,
                "created_at": t.created_at
            }
            for t in tasks
        ]
    }


# Эндпоинт для получения одной задачи по ID
@router.get("/tasks/{task_id}/", response_model=dict)
def get_task(task_id: int, db: Session = Depends(get_db)):
    logger.info(f"Получен запрос на получение задачи с id={task_id}")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        logger.warning(f"Задача с id={task_id} не найдена")
        raise HTTPException(status_code=404, detail="Задача не найдена")
    logger.info(f"Задача найдена: id={task.id}, title={task.title}")
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_completed": task.is_completed,
        "created_at": task.created_at,
    }


# Эндпоинт для обновления задачи по ID
@router.put("/tasks/{task_id}/", response_model=dict)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    logger.info(f"Получен запрос на обновление задачи с id={task_id}")

    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        logger.warning(f"Задача с id={task_id} не найдена")
        raise HTTPException(status_code=404, detail="Задача не найдена")

    logger.info(f"Обновляем задачу с id={task_id}")

    if task_update.title is not None:
        logger.info(f"Изменяем title: {task.title} -> {task_update.title}")
        task.title = task_update.title

    if task_update.description is not None:
        logger.info(f"Изменяем description")
        task.description = task_update.description

    if task_update.is_completed is not None:
        logger.info(f"Изменяем статус is_completed: {task.is_completed} -> {task_update.is_completed}")
        task.is_completed = task_update.is_completed

    db.commit()
    db.refresh(task)
    logger.info(f"Задача успешно обновлена: id={task.id}")
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


# Эндпоинт для удаления задачи
@router.delete("/tasks/{task_id}/", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    logger.info(f"Получен запрос на удаление задачи с id={task_id}")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        logger.warning(f"Задача с id={task_id} не найдена")
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    logger.info(f"Задача с id={task_id} успешно удалена")

    return {"message": "Задача успешно удалена"}
