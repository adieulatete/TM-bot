from typing import Iterable
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

from . import config
from .exceptions import PastDateError


# Setting up a connection to a SQLite database
DATABASE_URL = f"sqlite:///{config.SQLITE_DB_FILE}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Task model using SQLAlchemy ORM
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default="Не выполнена")
    celery_task_id = Column(String, nullable=True)

# Creating tables in the database
Base.metadata.create_all(bind=engine)


class TaskManager:
    def __init__(self):
        self.db = SessionLocal()

    def add_task(self, user_id: int, description: str, due_date: datetime, celery_task_id: str = None) -> Task:
        """Adding a new task for the user."""
        # Check for a previous date
        if due_date < datetime.now():
            raise PastDateError()
        
        task = Task(user_id=user_id, description=description, due_date=due_date, celery_task_id=celery_task_id)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_tasks(self, user_id: int) -> Iterable[Task]:
        """Retrieving all tasks for a specific user."""
        return self.db.query(Task).filter(Task.user_id == user_id).all()
    
    def get_task(self, task_id: int) -> Task:
        """Retrieving all tasks for a specific user."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task(self, task_id: int, description: str = None, due_date: datetime = None, status: str = None, celery_task_id: str = None) -> Task:
        """Update the task description, due date, or status."""
        # Check for a previous date
        if due_date is not None and due_date < datetime.now():
            raise PastDateError()

        task = self.db.query(Task).filter(Task.id == task_id).first()
        if description:
            task.description = description
        if due_date:
            task.due_date = due_date
        if status:
            task.status = status
        if celery_task_id:
            task.celery_task_id = celery_task_id
        self.db.commit()
        return task

    def delete_task(self, task_id: int) -> None:
        """Deleting a task by ID."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        self.db.delete(task)
        self.db.commit()
