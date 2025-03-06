from pydantic import BaseModel
from typing import Optional


# Базовая схема — общая для всех операций (создание, обновление)
class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


# Схема для создания задачи — требует title обязательно
class TaskCreate(TaskBase):
    title: str


# Схема для обновления задачи — все поля опциональны
class TaskUpdate(TaskBase):
    pass
