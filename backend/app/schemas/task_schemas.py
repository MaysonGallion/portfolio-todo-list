from pydantic import BaseModel, Field
from typing import Optional


# Базовая схема — общая для всех операций (создание, обновление)
class TaskBase(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    is_completed: Optional[bool] = None


# Схема для создания задачи — требует title обязательно
class TaskCreate(TaskBase):
    title: str = Field(..., min_length=3, max_length=100)


# Схема для обновления задачи — все поля опциональны
class TaskUpdate(TaskBase):
    pass
