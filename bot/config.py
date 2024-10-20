import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

SQLITE_DB_FILE = BASE_DIR.parent / "db.sqlite3"

TEMPLATES_DIR = BASE_DIR / "templates"
