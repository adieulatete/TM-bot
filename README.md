## WB-products

### General information about the project
Telegram bot for task management

#### Functional
  
• Adding a task: The user has the ability to add a new task with a description and due date;  
• View tasks: The user has the opportunity to view a list of all his tasks indicating the status (completed/not completed) and due date;  
• Update a task: The user has the ability to update the status of a task (for example, mark it as completed) or change the description and due date;  
• Removing a task: The user has the ability to delete a task from the list;  
• Reminders: The bot sends reminders to the user about tasks that are approaching due dates (for example, 1 day before the due date).  


#### Technologies used

`Python`, `SQLite`, `Git`, `Docker`, `Celery`, `Redis`

#### Libraries used

[`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot),
[`SQLAclchemy`](https://github.com/sqlalchemy/sqlalchemy),
[`Redis`](https://github.com/redis/redis),
[`Celery`](https://github.com/celery/celery),
[`Jinja2`](https://github.com/pallets/jinja),

### Deploy 

```bash
cd ~
git clone https://github.com/adieulatete/tm-bot.git
cd ~/tm-bot
```

Copy .env.example to .env and edit the .env file, filling it with all the environment variables:
```bash
cp .env.example .env
vim .env
```

Launching the application
```bash
docker-compose up --build -d
```
