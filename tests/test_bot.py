import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from unittest.mock import patch

from bot.celery import schedule_task_reminder
from bot.tasks import TaskManager, Task
from bot.exceptions import PastDateError

# Create an in-memory test database
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope='function')
def test_db():
    """Fixture for creating a test database."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create tables in the test database
    Task.metadata.create_all(bind=engine)
    
    yield session  # Provide the session for use in tests
    
    # Close the session after tests are done
    session.close()


@pytest.fixture
def task_manager(test_db):
    """Fixture for TaskManager using the test database."""
    manager = TaskManager()
    manager.db = test_db
    return manager


def test_add_task(task_manager):
    """Test for adding a new task."""
    task_manager.add_task(1, "Test task", datetime(2024, 12, 31, 20))
    tasks = task_manager.get_tasks(1)
    
    assert len(tasks) == 1
    assert tasks[0].description == "Test task"
    assert tasks[0].due_date.strftime('%Y-%m-%d-%H') == "2024-12-31-20"
    assert tasks[0].status == "Не выполнена"


def test_get_tasks(task_manager):
    """Test for retrieving all tasks for a user."""
    task_manager.add_task(1, "Task 1", datetime.now() + timedelta(days=1))
    task_manager.add_task(1, "Task 2", datetime.now() + timedelta(days=3))
    
    tasks = task_manager.get_tasks(1)
    
    assert len(tasks) == 2
    assert tasks[0].description == "Task 1"
    assert tasks[1].description == "Task 2"


def test_update_task(task_manager):
    """Test for updating the description and status of a task."""
    task = task_manager.add_task(1, "Task to update", datetime.now() + timedelta(days=5))
    
    updated_task = task_manager.update_task(task.id, description="Updated task", status="Выполнена")
    
    assert updated_task.description == "Updated task"
    assert updated_task.status == "Выполнена"


def test_delete_task(task_manager):
    """Test for deleting a task."""
    task = task_manager.add_task(1, "Task to delete", datetime(2024, 12, 15, 12))
    
    task_manager.delete_task(task.id)
    tasks = task_manager.get_tasks(1)
    
    assert len(tasks) == 0


@patch('bot.celery.schedule_task_reminder.apply_async')
def test_schedule_task_reminder(mock_apply_async, task_manager):
    """Test for scheduling a reminder using Celery."""
    task = task_manager.add_task(1, "Task with reminder", datetime(2024, 12, 20, 12) - timedelta(days=1))
    
    # Call the function to schedule the reminder
    schedule_task_reminder.apply_async((1, task.id), eta=task.due_date)
    
    # Verify that the Celery task was called
    mock_apply_async.assert_called_once_with((1, task.id), eta=task.due_date)


def test_add_task_with_past_due_date(task_manager):
    """Test for adding a task with a past due date."""
    with pytest.raises(PastDateError):
        task_manager.add_task(1, "Task with past due date", datetime.now() - timedelta(minutes=5))


def test_update_task_with_past_due_date(task_manager):
    """Test for updating a task with a past due date."""
    task = task_manager.add_task(1, "Task to update", datetime(2024, 12, 10, 15))
    
    with pytest.raises(PastDateError):
        task_manager.update_task(task.id, due_date=datetime.now() - timedelta(minutes=5))
        