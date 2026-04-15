#!/usr/bin/env python3
"""
Скрипт импорта датасета Book-Crossing в базу данных
"""

import pandas as pd
import pymysql
import os
from dotenv import load_dotenv
import sys

# Загружаем переменные окружения
load_dotenv()

print("🚀 Начинаем импорт Book-Crossing датасета...")

# Настройки подключения к БД
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'bookuser'),
    'password': os.getenv('DB_PASS', 'bookpassword'),
    'database': os.getenv('DB_NAME', 'book_recommender')
}

print(f"📡 Подключение к {DB_CONFIG['host']}:{DB_CONFIG['port']}...")

try:
    # Подключаемся к MySQL
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Подключено к базе данных!")
    
    # Очищаем старые данные
    print("️  Очищаем старые данные...")
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
    
    # Добавляем жанры (упрощённо)
    print("📚 Добавляем жанры...")
    genres = [
        'Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Fantasy',
        'Biography', 'History', 'Thriller', 'Horror', 'Poetry'
    ]
    for genre in genres:
        cursor.execute("INSERT INTO Genres (genre_name) VALUES (%s)", (genre,))
    conn.commit()
    print(f"✅ Добавлено {len(genres)} жанров")
    
    # Импортируем книги
    print("📖 Импортируем книги...")
    try:
        books_df = pd.read_csv('data/BX-Books.csv', sep=';', encoding='latin-1', 
                               on_bad_lines='skip', low_memory=False)
    except FileNotFoundError:
        print("❌ Файл BX-Books.csv не найден!")
        print("💡 Убедитесь, что скачали и распаковали датасет в папку data/")
        sys.exit(1)
    
    print(f"   Найдено {len(books_df)} книг в файле")
    
    # Берём первые 10000 книг (для скорости)
    books_df = books_df.head(10000)
    
    books_imported = 0
    for idx, row in books_df.iterrows():
        try:
            isbn = str(row['ISBN']).strip()
            title = str(row['Book-Title']).strip()[:260]
            author = str(row['Book-Author']).strip()[:260]
            year = row['Year-Of-Publication']
            publisher = str(row['Publisher']).strip()[:60] if pd.notna(row['Publisher']) else None
            
            # Пропускаем пустые
            if not isbn or isbn == '' or not title or title == '':
                continue
            
            # Очищаем год
            try:
                year = int(year) if pd.notna(year) and str(year).isdigit() else None
            except:
                year = None
            
            cursor.execute("""
                INSERT INTO Book (isbn, title, author, year_publication, publisher, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (isbn, title, author, year, publisher, '/images/no-cover.jpg'))
            
            books_imported += 1
            
            if books_imported % 1000 == 0:
                print(f"   📚 Импортировано {books_imported} книг...")
                
        except Exception as e:
            continue
    
    conn.commit()
    print(f"✅ Импортировано {books_imported} книг")
    
    # Импортируем пользователей
    print("👥 Импортируем пользователей...")
    try:
        users_df = pd.read_csv('data/BX-Users.csv', sep=';', encoding='latin-1',
                               on_bad_lines='skip')
    except FileNotFoundError:
        print("⚠️  Файл BX-Users.csv не найден, пропускаем...")
        users_df = pd.DataFrame()
    
    users_imported = 0
    if len(users_df) > 0:
        users_df = users_df.head(50000)  # Берём 50000 пользователей
        
        for idx, row in users_df.iterrows():
            try:
                user_id = int(row['User-ID'])
                location = str(row['Location']).strip()[:100] if pd.notna(row['Location']) else ''
                age = int(row['Age']) if pd.notna(row['Age']) and str(row['Age']).isdigit() else None
                
                cursor.execute("""
                    INSERT INTO Users (user_id, login, password_hash, age, location)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, f'user_{user_id}', 'hash', age, location))
                
                users_imported += 1
                
                if users_imported % 5000 == 0:
                    print(f"   👥 Импортировано {users_imported} пользователей...")
                    
            except Exception as e:
                continue
        
        conn.commit()
    
    print(f"✅ Импортировано {users_imported} пользователей")
    
    # Импортируем оценки
    print("⭐ Импортируем оценки...")
    try:
        ratings_df = pd.read_csv('data/BX-Book-Ratings.csv', sep=';', encoding='latin-1',
                                 on_bad_lines='skip')
    except FileNotFoundError:
        print("❌ Файл BX-Book-Ratings.csv не найден!")
        sys.exit(1)
    
    print(f"   Найдено {len(ratings_df)} оценок в файле")
    
    # Берём первые 100000 оценок (для скорости)
    ratings_df = ratings_df.head(100000)
    
    ratings_imported = 0
    for idx, row in ratings_df.iterrows():
        try:
            user_id = int(row['User-ID'])
            isbn = str(row['ISBN']).strip()
            rating = int(row['Book-Rating'])
            
            # Пропускаем нулевые оценки
            if rating == 0:
                continue
            
            # Находим книгу по ISBN
            cursor.execute("SELECT book_id FROM Book WHERE isbn = %s LIMIT 1", (isbn,))
            result = cursor.fetchone()
            
            if result:
                book_id = result[0]
                
                cursor.execute("""
                    INSERT INTO Ratings (user_id, book_id, rating, rated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE rating = rating
                """, (user_id, book_id, rating))
                
                ratings_imported += 1
                
                if ratings_imported % 10000 == 0:
                    print(f"   ⭐ Импортировано {ratings_imported} оценок...")
                    
        except Exception as e:
            continue
    
    conn.commit()
    print(f"✅ Импортировано {ratings_imported} оценок")
    
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
    print("="*50)
    
    cursor.close()
    conn.close()
    
    print("\n✅ Импорт завершён успешно!")
    print("💡 Не забудьте перезапустить ML-сервис:")
    print("   docker-compose restart ml-service")
    
except Exception as e:
    print(f"\n❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)