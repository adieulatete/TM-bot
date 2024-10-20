import logging

from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    Defaults,
    ConversationHandler
)

from .handlers import *
from .  import config


logging.basicConfig(
    filename='bot.log',
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

ADDING_TASK_DESC, ADDING_TASK_DUE_DATE, UPDATING_TASK_DESC, UPDATING_TASK_DUE_DATE = range(4)


if __name__ == "__main__":
    defaults = Defaults(parse_mode=ParseMode.HTML)
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).defaults(defaults).build()

    app.add_handler(CommandHandler("start", start))

    add_task_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Добавить задачу"), add_task_start)],
        states={
            ADDING_TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_desc)],
            ADDING_TASK_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_due_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    update_task_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern=r"^update_\d+$")],
        states={
            UPDATING_TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_task_desc)],
            UPDATING_TASK_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_task_due_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )


    app.add_handlers([add_task_handler, update_task_handler])
    app.add_handler(MessageHandler(filters.Regex("Посмотреть задачи"), view_tasks))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
