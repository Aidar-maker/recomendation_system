from sqlalchemy import create_engine
import os

def get_db_connection():
    """
    Создаёт подключение к базе данных
    URL берётся из переменных окружения (docker-compose.yml)
    """
    # Формат: mysql+pymysql://user:password@host:port/database
    database_url = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://bookuser:bookpassword@db:3306/book_recommender'
    )
    
    # Создаём движок SQLAlchemy
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=False  # Отключить логирование SQL-запросов
    )
    
    return engine.connect()