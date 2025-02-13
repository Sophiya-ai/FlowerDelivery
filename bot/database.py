import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'db' / 'db.sqlite3'


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
