from sqlalchemy import create_engine
from app.core.config import config

db_conn_str = f'postgresql+psycopg2://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_SCHEMA}'
pg_engine = None

if pg_engine is None:
    pg_engine = create_engine(db_conn_str)