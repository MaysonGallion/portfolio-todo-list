from fastapi import FastAPI
from app.database.database import SessionLocal
from sqlalchemy import text
from app.routes.task_routes import router as task_router

app = FastAPI()


@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "Подключение к базе данных успешно"}
    except Exception as e:
        return {"status": "Ошибка подключения к базе данных", "details": str(e)}


app.include_router(task_router)
