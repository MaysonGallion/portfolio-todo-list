from ..database.database import Base, engine
from ..models.task import Task


def init_db():
    Base.metadata.create_all(bind=engine)
