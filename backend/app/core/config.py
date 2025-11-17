import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

ROOT = Path(__file__).parent.parent.parent

load_dotenv(dotenv_path=ROOT / '.env', verbose=True)

@dataclass
class Config:
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_USER = os.environ.get('DB_USER')
    DB_PASS = os.environ.get('DB_PASS')
    DB_SCHEMA = os.environ.get('DB_SCHEMA')
    OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')
    GOOGLE_AI_KEY = os.environ.get('GOOGLE_AI_KEY')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


config = Config()