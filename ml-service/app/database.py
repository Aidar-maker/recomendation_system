from sqlalchemy import create_engine
import os

# Глобальный движок (создаётся один раз)
_engine = None

def get_engine():
    """Singleton движок SQLAlchemy"""
    global _engine
    if _engine is None:
        database_url = os.getenv(
            'DATABASE_URL', 
            'mysql+pymysql://bookuser:bookpassword@db:3306/book_recommender'
        )
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
    return _engine

def get_db_connection():
    """Возвращает активное соединение (не забывай закрывать!)"""
    return get_engine().connect()