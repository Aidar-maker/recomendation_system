from sqlalchemy import create_engine
import os

def get_db_connection():
    engine = create_engine(
        "mysql+pymysql://bookuser:bookpassword@db:3306/book_recommender",
        pool_pre_ping=True
    )
    return engine.connect()