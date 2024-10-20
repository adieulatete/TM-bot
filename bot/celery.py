import logging
import asyncio
from telegram import Bot

from celery import Celery
from celery.contrib.abortable import AbortableAsyncResult
from celery.contrib.abortable import AbortableTask

from .tasks import TaskManager
from . import config
from .templates import render_message

celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

task_manager = TaskManager()

@celery_app.task(base=AbortableTask)
def schedule_task_reminder(user_id: int, task_id: int) -> None:
    """Background task for task reminder."""
    
    task = task_manager.get_task(task_id)
    if task:
        message = render_message(
            'reminder_message',
            task_description=task.description,
            due_date=task.due_date.strftime('%Y-%m-%d %H:%M')
        )
        
        # Sending a reminder via Telegram API
        bot = Bot(token=config.TELEGRAM_TOKEN)
        async def send_message():
            await bot.send_message(chat_id=user_id, text=message)

        # Schedule the send_message function as a new task)
        asyncio.run(send_message())

        logging.info(f"A reminder was sent to {user_id} about task {task_id}")


def revoke_task(user_id: int, task_id: int) -> None:
    """Delete a Celery task."""
    task = task_manager.get_task(task_id)
    result = AbortableAsyncResult(task.celery_task_id)
    result.abort()
    logging.info(f"The reminder for the {user_id} about the task {task_id} was canceled.")
