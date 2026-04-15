#!/usr/bin/env python3
"""
Импорт Kaggle Books Dataset
Структура:
- books.csv: книги
- users.csv: пользователи  
- ratings.csv: оценки (0-10, нужно преобразовать в 1-5)
"""

import pandas as pd
import pymysql
import os
from dotenv import load_dotenv
import sys

print("🚀 Импортируем Kaggle Books Dataset...")

# Подключение к БД
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'bookuser',
    'password': 'bookpassword',
    'database': 'book_recommender'
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Подключено к базе данных")
    
    # Очищаем данные
    print("🗑️  Очищаем старые данные...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE Ratings")
    cursor.execute("TRUNCATE TABLE User_Preferences")
    cursor.execute("TRUNCATE TABLE Book_Genres")
    cursor.execute("TRUNCATE TABLE Book")
    cursor.execute("TRUNCATE TABLE Users")
    cursor.execute("TRUNCATE TABLE Genres")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("✅ Очистка завершена")
    
    # Добавляем жанры
    print("📚 Добавляем жанры...")
    genres = ['Fiction', 'Mystery', 'Romance', 'Sci-Fi', 'Fantasy', 
              'Biography', 'History', 'Thriller', 'Horror', 'Poetry']
    for genre in genres:
        cursor.execute("INSERT INTO Genres (genre_name) VALUES (%s)", (genre,))
    conn.commit()
    
    # Импортируем книги
    print("📖 Импортируем книги из books.csv...")
    books_df = pd.read_csv('data/books.csv', sep=';')
    print(f"   Найдено {len(books_df)} книг")
    
    books_imported = 0
    isbn_to_book_id = {}  # Словарь для связи с оценками
    
    for idx, row in books_df.iterrows():
        try:
            isbn = str(row.get('ISBN', '')).strip()
            title = str(row.get('Book-Title', row.get('Title', ''))).strip()[:260]
            author = str(row.get('Book-Author', row.get('Author', ''))).strip()[:260]
            year = row.get('Year-Of-Publication', row.get('Year', 2000))
            publisher = str(row.get('Publisher', '')).strip()[:60]
            
            if not isbn or not title:
                continue
            
            cursor.execute("""
                INSERT INTO Book (isbn, title, author, year_publication, publisher, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (isbn, title, author, int(year) if str(year).isdigit() else None, 
                  publisher, '/images/no-cover.jpg'))
            
            book_id = cursor.lastrowid
            isbn_to_book_id[isbn] = book_id
            books_imported += 1
            
            if books_imported % 1000 == 0:
                print(f"   📚 Импортировано {books_imported} книг...")
                
        except Exception as e:
            continue
    
    conn.commit()
    print(f"✅ Импортировано {books_imported} книг")
    
    # Импортируем пользователей
    print("👥 Импортируем пользователей из users.csv...")
    users_df = pd.read_csv('data/users.csv', sep=';')
    print(f"   Найдено {len(users_df)} пользователей")
    
    users_imported = 0
    user_id_map = {}  # Старый ID -> новый ID
    
    for idx, row in users_df.iterrows():
        try:
            old_user_id = int(row.get('User-ID', 0))
            location = str(row.get('Location', '')).strip()[:100]
            age = row.get('Age', None)
            
            # Очищаем возраст
            try:
                age = int(age) if pd.notna(age) and str(age).isdigit() and 0 < age < 120 else None
            except:
                age = None
            
            cursor.execute("""
                INSERT INTO Users (user_id, login, password_hash, age, location)
                VALUES (%s, %s, %s, %s, %s)
            """, (old_user_id, f'user_{old_user_id}', 'hash', age, location))
            
            user_id_map[old_user_id] = old_user_id
            users_imported += 1
            
            if users_imported % 5000 == 0:
                print(f"   👥 Импортировано {users_imported} пользователей...")
                
        except Exception as e:
            continue
    
    conn.commit()
    print(f"✅ Импортировано {users_imported} пользователей")
    
    # Импортируем оценки
    print("⭐ Импортируем оценки из ratings.csv...")
    ratings_df = pd.read_csv('data/ratings.csv', sep=';')
    print(f"   Найдено {len(ratings_df)} оценок")
    
    # Фильтруем: оставляем только оценки > 0 (0 = нет оценки)
    ratings_df = ratings_df[ratings_df['Book-Rating'] > 0]
    print(f"   После фильтрации (rating > 0): {len(ratings_df)} оценок")
    
    ratings_imported = 0
    skipped_no_book = 0
    
    for idx, row in ratings_df.iterrows():
    try:
        user_id = int(row.get('User-ID', 0))
        isbn = str(row.get('ISBN', '')).strip()
        rating_new = int(row.get('Book-Rating', 0))
            
        # Пропускаем нулевые оценки (0 = не оценено)
        if rating_new == 0:
            continue
            
        # Проверяем что рейтинг в диапазоне 0-10
        if rating_new < 0 or rating_new > 10:
            continue
            
        # Находим book_id по ISBN
        book_id = isbn_to_book_id.get(isbn)
            
        if not book_id:
            skipped_no_book += 1
            continue
            
        cursor.execute("""
            INSERT INTO Ratings (user_id, book_id, rating, rated_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE rating = rating
        """, (user_id, book_id, rating_new))
            
        ratings_imported += 1
            
        if ratings_imported % 10000 == 0:
            print(f"   ⭐ Импортировано {ratings_imported} оценок...")
                
    except Exception as e:
        continue
    
    conn.commit()
    print(f"✅ Импортировано {ratings_imported} оценок")
    if skipped_no_book > 0:
        print(f"   ⚠️  Пропущено {skipped_no_book} оценок (книга не найдена)")
    
    # Статистика
    print("\n" + "="*50)
    print("📊 ИТОГИ ИМПОРТА:")
    print("="*50)
    cursor.execute("SELECT COUNT(*) FROM Book")
    print(f"📚 Книг: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Users")
    print(f"👥 Пользователей: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Ratings")
    print(f"⭐ Оценок: {cursor.fetchone()[0]}")
    cursor.execute("SELECT MIN(rating), MAX(rating), AVG(rating) FROM Ratings")
    min_r, max_r, avg_r = cursor.fetchone()
    print(f"📈 Рейтинг: min={min_r}, max={max_r}, avg={avg_r:.2f}")
    print("="*50)
    
    cursor.close()
    conn.close()
    
    print("\n✅ Импорт завершён успешно!")
    print("💡 Перезапустите ML-сервис:")
    print("   docker-compose restart ml-service")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()