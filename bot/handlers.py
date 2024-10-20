import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler
)

from .tasks import TaskManager, Task
from .keyboards import main_keyboard, task_action_keyboard
from .exceptions import PastDateError 
from .celery import schedule_task_reminder, revoke_task
from .templates import render_message

task_manager = TaskManager()

ADDING_TASK_DESC, ADDING_TASK_DUE_DATE, UPDATING_TASK_DESC, UPDATING_TASK_DUE_DATE = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu to the user and logs the interaction."""
    user_id = update.message.from_user.id
    await update.message.reply_text(render_message('welcome_message'))
    await update.message.reply_text(
        render_message('choose_action_message'),
        reply_markup=main_keyboard()
    )
    logging.info(f"User {user_id} accessed the main menu.")


async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the task addition process."""
    user_id = update.message.from_user.id
    await update.message.reply_text(render_message('enter_task_desc_message'))
    logging.info(f"User {user_id} started adding a task.")
    return ADDING_TASK_DESC


async def add_task_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages for task details."""
    user_id = update.message.from_user.id

    context.user_data['task_desc'] = update.message.text
    await update.message.reply_text(
        render_message('enter_due_date_message')
    )
    logging.info(f"User {user_id} entered task description: {context.user_data['task_desc']}")
    return ADDING_TASK_DUE_DATE
        

async def add_task_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages for task details."""
    user_id = update.message.from_user.id
    try:
        task_due_date = datetime.strptime(update.message.text, '%Y-%m-%d-%H')

        task = task_manager.add_task(user_id, context.user_data['task_desc'], task_due_date)
        
        await update.message.reply_text(
            render_message(
                'task_added_message',
                task_desc=context.user_data['task_desc'], due_date=task_due_date.strftime('%Y-%m-%d %H:%M')
            )
        )

        logging.info(f"Task added for user {user_id}: {context.user_data['task_desc']} with due date {task_due_date}")

        _prepair_schedule_task_reminder(user_id, task)

        # Reset User State
        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            render_message('invalid_date_format_message')
        )
        logging.warning(f"User {user_id} entered invalid date format: {update.message.text}")
    except PastDateError as e:
        await update.message.reply_text(str(e))
        logging.warning(f"User {user_id} entered a past date: {update.message.text}")


async def update_task_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages for task details."""
    user_id = update.message.from_user.id
    task_id = context.user_data['task_id']
    new_desc = update.message.text
    await update.message.reply_text(
        render_message('enter_new_due_date_message')
    )
    context.user_data['new_desc'] = new_desc
    logging.info(f"User {user_id} entered new description for task {task_id}: {new_desc}")
    return UPDATING_TASK_DUE_DATE


async def update_task_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages for task details."""
    user_id = update.message.from_user.id
    task_id = context.user_data['task_id']
    new_due_date = update.message.text
    try:
        new_due_date = datetime.strptime(new_due_date, '%Y-%m-%d-%H')

        task = task_manager.update_task(task_id, description=context.user_data['new_desc'], due_date=new_due_date)

        await update.message.reply_text(
            render_message(
                'task_update_message',
                task_desc=task.description,
                due_date=task.due_date.strftime('%Y-%m-%d %H:%M')
            )
        )
        logging.info(f"Task {task_id} updated by user {user_id}: {context.user_data['new_desc']} with new due date {new_due_date}")

        revoke_task(user_id=user_id, task_id=task.id)
        _prepair_schedule_task_reminder(user_id, task)

        # Reset User State
        context.user_data.clear()
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            render_message('invalid_date_format_message')
        )
        logging.warning(f"User {user_id} entered invalid date format for due date: {new_due_date}")
    except PastDateError as e:
        await update.message.reply_text(str(e))
        logging.warning(f"User {user_id} entered a past date for task {task_id}: {new_due_date}")


async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays one task per page with action buttons and pagination."""
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    page = context.user_data.get('page', 0)  # Current page
    tasks = task_manager.get_tasks(user_id)

    if tasks:
        total_tasks = len(tasks)

        page %= total_tasks  # Cycle through pages

        task : Task = tasks[page]
        task_message = render_message(
            'task_message',
            task_description=task.description,
            due_date=task.due_date.strftime('%Y-%m-%d %H:%M'),
            task_status=task.status,
        )
        
        if update.message:
            await update.message.reply_text(task_message, reply_markup=task_action_keyboard(task.id, page, total_tasks))
        elif update.callback_query:
            await update.callback_query.edit_message_text(task_message, reply_markup=task_action_keyboard(task.id, page, total_tasks))

        logging.info(f"Displayed task {task.id} for user {user_id}, page {page + 1}/{total_tasks}.")
    else:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                render_message('no_tasks_found')
            )
        else:
            await update.message.reply_text(
                render_message('no_tasks_found')
            )
        logging.info(f"No tasks found for user {user_id}.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks for task actions and pagination."""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    try:
        match data:
            case data if data.startswith("update"):
                task_id = int(data.split("_")[-1])
                await query.message.reply_text(
                    render_message('enter_new_task_desc_message')
                )
                context.user_data['task_id'] = task_id
                logging.info(f"User {user_id} selected to update task {task_id}.")
                return UPDATING_TASK_DESC

            case data if data.startswith("mark_done"):
                task_id = int(data.split("_")[-1])
                task = task_manager.get_task(task_id)
                if task.status == 'Выполнена':
                    return
                task_manager.update_task(task_id, status='Выполнена')
                await view_tasks(update, context)
                logging.info(f"User {user_id} marked task {task_id} as completed.")

            case data if data.startswith("delete"):
                task_id = int(data.split("_")[-1])
                revoke_task(user_id=user_id, task_id=task_id)
                task_manager.delete_task(task_id)
                
                logging.info(f"User {user_id} deleted task {task_id}.")
                
                tasks = task_manager.get_tasks(user_id)
                if tasks:
                    await view_tasks(update, context) 
                else:
                    await query.message.edit_text(
                        render_message('no_tasks_found')
                    )        
            case data if data.startswith("next_page"):
                tasks = task_manager.get_tasks(user_id)
                if len(tasks) > 1:
                    # Go to next page with loop
                    context.user_data['page'] = (context.user_data.get('page', 0) + 1) % len(tasks)
                    await view_tasks(update, context)
                    logging.info(f"User {user_id} navigated to the next page.")
                else:
                    # Do nothing or display a message if only one task exists
                    await update.callback_query.answer(
                        render_message('task_list_warning')
                    )

            case data if data.startswith("prev_page"):
                tasks = task_manager.get_tasks(user_id)
                if len(tasks) > 1:
                    # Go to previous page with loop
                    context.user_data['page'] = (context.user_data.get('page', 0) - 1) % len(tasks)
                    await view_tasks(update, context)
                    logging.info(f"User {user_id} navigated to the previous page.")
                else:
                    # Do nothing or display a message if only one task exists
                    await update.callback_query.answer(
                        render_message('task_list_warning')
                    )
    
    except (IndexError, ValueError):
        await query.message.reply_text(
            render_message('incorrect_data_error_message')
        )
        logging.error(f"Invalid task ID or action in callback data: {data}")
    except Exception as e:
        await query.message.reply_text(
            render_message('error_during_operation')
        )
        logging.error(f"Error handling task action for user {user_id}: {str(e)}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation."""
    context.user_data.clear()
    return ConversationHandler.END

def _prepair_schedule_task_reminder(user_id: int, task: Task) -> None:
    """Preparation for setting the celery task"""
    eta = task.due_date - timedelta(days=1)
    if eta >= datetime.now():
        celery_task = schedule_task_reminder.apply_async((user_id, task.id), eta=eta)
        task_manager.update_task(task_id=task.id, celery_task_id=celery_task.id)
    else:
        schedule_task_reminder.apply_async((user_id, task.id))
