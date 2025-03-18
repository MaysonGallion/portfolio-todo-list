from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.task import Task
from ..schemas.task_schemas import TaskCreate, TaskUpdate, TaskListResponse, TaskBulkDelete
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


def get_task_or_404(task_id: int, db: Session):
    """Функция для получения задачи по ID или выбрасывания ошибки 404"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        logger.warning(f"❌ Ошибка: Задача с ID {task_id} не найдена")
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.post("/tasks/", response_model=dict)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Создание новой задачи"""
    logger.info(f"Получен запрос на создание задачи: {task.title}")

    new_task = Task(title=task.title, description=task.description)
    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        logger.info(f"✅ Задача создана: id={new_task.id}, title={new_task.title}")
        return {"message": "Задача успешно создана!", "task_id": new_task.id}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при создании задачи: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка создания задачи")


@router.get("/tasks/", response_model=TaskListResponse)
def get_tasks(
        db: Session = Depends(get_db),
        is_completed: Optional[bool] = Query(None, description="Фильтр: true - выполненные, false - невыполненные"),
        q: Optional[str] = Query(None, min_length=2, description="Поиск по названию задачи (не менее 2 символов)"),
        page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
        size: int = Query(5, ge=1, le=100, description="Количество задач на странице (по умолчанию 5, макс. 100)")
):
    """Получение всех задач с фильтрацией и пагинацией"""
    logger.info(f"📌 Запрос задач: стр. {page}, размер {size}, фильтр по статусу={is_completed}, поиск={q}")

    query = db.query(Task)

    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    if q:
        query = query.filter(Task.title.ilike(f"%{q}%"))

    total_tasks = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset((page - 1) * size).limit(size).all()

    logger.info(f"✅ Загружено {len(tasks)} задач из {total_tasks} (стр. {page})")

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


@router.get("/tasks/{task_id}/", response_model=dict)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Получение задачи по ID"""
    logger.info(f"Получен запрос на получение задачи с id={task_id}")
    task = get_task_or_404(task_id, db)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "is_completed": task.is_completed,
        "created_at": task.created_at,
    }


@router.put("/tasks/{task_id}/", response_model=dict)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Обновление задачи по ID"""
    logger.info(f"Получен запрос на обновление задачи с id={task_id}")

    task = get_task_or_404(task_id, db)

    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        logger.info(f"🔄 Изменяем {key}: {getattr(task, key)} -> {value}")
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    logger.info(f"✅ Задача успешно обновлена: id={task.id}")

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


@router.delete("/tasks/{task_id}/", response_model=dict)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удаление одной задачи"""
    logger.info(f"Получен запрос на удаление задачи с id={task_id}")

    task = get_task_or_404(task_id, db)

    try:
        db.delete(task)
        db.commit()
        logger.info(f"✅ Задача с id={task_id} успешно удалена")
        return {"message": "Задача успешно удалена", "deleted_task_id": task_id}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при удалении задачи {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка удаления задачи")


@router.delete("/tasks/bulk-delete", response_model=dict)
def bulk_delete_tasks(task_data: TaskBulkDelete = Body(...), db: Session = Depends(get_db)):
    """Удаление нескольких задач по списку ID"""
    logger.info(f"✅ Получен запрос на массовое удаление задач: {task_data.task_ids}")

    unique_task_ids = list(set(task_data.task_ids))
    existing_task_ids = {task_id for task_id, in db.query(Task.id).filter(Task.id.in_(unique_task_ids)).all()}
    deleted_ids = list(existing_task_ids)
    not_found_ids = list(set(unique_task_ids) - existing_task_ids)

    if not deleted_ids:
        logger.warning(f"❌ Не найдено ни одной задачи из переданных ID: {not_found_ids}")
        raise HTTPException(status_code=404, detail="Задачи не найдены")

    try:
        db.query(Task).filter(Task.id.in_(deleted_ids)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"✅ Успешно удалены: {deleted_ids}")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при удалении задач: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка удаления задач")

    return {"deleted": deleted_ids, "not_found": not_found_ids}
