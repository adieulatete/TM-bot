from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the keyboard with the main menu."""
    keyboard = [
        [KeyboardButton("Добавить задачу"), KeyboardButton("Посмотреть задачи")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def task_action_keyboard(task_id: int, current_page: int, total_tasks: int) -> InlineKeyboardMarkup:
    """Returns the inline keyboard for updating and deleting a task with pagination info."""
    keyboard = [
        [InlineKeyboardButton("🔄", callback_data=f"update_{task_id}"),
         InlineKeyboardButton("🗑", callback_data=f"delete_{task_id}"),
         InlineKeyboardButton("☑️", callback_data=f"mark_done_{task_id}")]
    ]

    # Navigation buttons
    navigation_buttons = [
        InlineKeyboardButton("⬅️", callback_data="prev_page"),
        InlineKeyboardButton(f"{current_page + 1}/{total_tasks}", callback_data="page_info"),  # Page counting
        InlineKeyboardButton("➡️", callback_data="next_page"),
    ]

    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(keyboard)
