#!/usr/bin/env python3
"""
Импорт Kaggle Books Dataset
CSV файлы:
- books.csv: ISBN, Book-Title, Book-Author, Year-Of-Publication, Publisher, Image-URL-*
- users.csv: User-ID, Location, Age
- ratings.csv: User-ID, ISBN, Book-Rating (0-10)
"""

import pandas as pd
import pymysql
import sys

print(" Импортируем Kaggle Books Dataset...")

# Подключение к БД (через Docker порт)
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'bookuser',
    'password': 'bookpassword',
    'database': 'book_recommender'
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(" Подключено к базе данных")
    
    # Очищаем данные
    print("  Очищаем старые данные...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE Ratings")
    cursor.execute("TRUNCATE TABLE User_Preferences")
    cursor.execute("TRUNCATE TABLE Book_Genres")
    cursor.execute("TRUNCATE TABLE Book")
    cursor.execute("TRUNCATE TABLE Users")
    cursor.execute("TRUNCATE TABLE Genres")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print(" Очистка завершена") 
        
    
    # Статистика
    print("\n" + "="*50)
    print(" ИТОГИ ОЧИСТИКИ:")
    print("="*50)
    cursor.execute("SELECT COUNT(*) FROM Book")
    print(f" Книг: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Users")
    print(f" Пользователей: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Ratings")
    print(f" Оценок: {cursor.fetchone()[0]}")
    cursor.execute("SELECT MIN(rating), MAX(rating), AVG(rating) FROM Ratings")
    print("="*50)
    
    cursor.close()
    conn.close()

except pymysql.err.OperationalError as e:
    print(f"\n Ошибка подключения к MySQL: {e}")

except Exception as e:
    print(f"\n Ошибка: {e}")
    import traceback
    traceback.print_exc()