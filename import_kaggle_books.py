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
    
    # Добавляем жанры
    print(" Добавляем жанры...")
    genres = ['Fiction', 'Mystery', 'Romance', 'Sci-Fi', 'Fantasy', 
              'Biography', 'History', 'Thriller', 'Horror', 'Poetry',
              'Classical', 'Mythology', 'Adventure', 'Drama']
    for genre in genres:
        cursor.execute("INSERT INTO Genres (genre_name) VALUES (%s)", (genre,))
    conn.commit()
    print(f" Добавлено {len(genres)} жанров")
    
    # Импортируем пользователей
    print(" Импортируем пользователей из users.csv...")
    try:
        users_df = pd.read_csv('data/users.csv', sep=';', encoding='latin-1')
        print(f"   Найдено {len(users_df)} пользователей")
        
        users_imported = 0
        errors = 0
        
        for idx, row in users_df.iterrows():
            try:
                user_id = int(row.get('User-ID', 0))
                location = str(row.get('Location', '')).strip()[:100] if pd.notna(row.get('Location')) else None
                age_val = row.get('Age')
                
                # Очищаем возраст
                try:
                    age = int(age_val) if pd.notna(age_val) and str(age_val).isdigit() and 0 < age_val < 120 else 25
                except:
                    age = 25
                
                cursor.execute("""
                    INSERT INTO Users (user_id, login, password_hash, age, location)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, f'user_{user_id}', 'hash', age, location))
                
                users_imported += 1
                
                if users_imported % 5000 == 0:
                    print(f"    Импортировано {users_imported} пользователей...")
                    conn.commit()  # Коммитим периодически
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Показываем первые 5 ошибок
                    print(f"     Ошибка пользователя {idx}: {e}")
                continue
        
        conn.commit()
        print(f" Импортировано {users_imported} пользователей (ошибок: {errors})")
        
    except FileNotFoundError:
        print("  users.csv не найден, пропускаем пользователей")
    
    # Импортируем книги
    print(" Импортируем книги из books.csv...")
    try:
        books_df = pd.read_csv('data/books.csv', sep=';', encoding='latin-1', 
                       on_bad_lines='skip')
        print(f"   Найдено {len(books_df)} книг")
        
        books_imported = 0
        isbn_to_book_id = {}
        
        for idx, row in books_df.iterrows():
            try:
                isbn = str(row.get('ISBN', '')).strip()
                title = str(row.get('Book-Title', '')).strip()[:260]
                author = str(row.get('Book-Author', '')).strip()[:260]
                year = row.get('Year-Of-Publication')
                publisher = str(row.get('Publisher', '')).strip()[:60] if pd.notna(row.get('Publisher')) else None
                image_url = str(row.get('Image-URL-S', '')).strip() if pd.notna(row.get('Image-URL-S')) else '/images/no-cover.jpg'
                
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
                """, (isbn, title, author, year, publisher, image_url))
                
                book_id = cursor.lastrowid
                isbn_to_book_id[isbn] = book_id
                books_imported += 1
                
                if books_imported % 10000 == 0:
                    print(f"    Импортировано {books_imported} книг...")
                    
            except Exception as e:
                continue
        
        conn.commit()
        print(f" Импортировано {books_imported} книг")
        
    except FileNotFoundError:
        print(" books.csv не найден!")
        sys.exit(1)
    
    # Импортируем оценки
    print(" Импортируем оценки из ratings.csv...")
    try:
        ratings_df = pd.read_csv('data/ratings.csv', sep=';', encoding='latin-1')
        print(f"   Найдено {len(ratings_df)} оценок")
        
        # Фильтруем: оставляем только оценки > 0 (0 = нет оценки)
        ratings_df = ratings_df[ratings_df['Book-Rating'] > 0]
        print(f"   После фильтрации (rating > 0): {len(ratings_df)} оценок")
        
        ratings_imported = 0
        skipped_no_book = 0
        skipped_no_user = 0
        
        for idx, row in ratings_df.iterrows():
            try:
                user_id = int(row.get('User-ID', 0))
                isbn = str(row.get('ISBN', '')).strip()
                rating_raw = row.get('Book-Rating', 0)
                
                # Очищаем рейтинг
                try:
                    rating = int(float(str(rating_raw).strip()))
                except:
                    continue
                
                # Пропускаем нули
                if rating == 0:
                    continue
                
                # Принимаем 1-10
                if rating < 1 or rating > 10:
                    continue
                
                book_id = isbn_to_book_id.get(isbn)
                
                if not book_id:
                    skipped += 1
                    continue
                
                cursor.execute("""
                    REPLACE INTO Ratings (user_id, book_id, rating, rated_at)
                    VALUES (%s, %s, %s, NOW())
                """, (user_id, book_id, rating))
                
                ratings_imported += 1
                
                if ratings_imported % 20000 == 0:
                    print(f"    {ratings_imported}...")
                    conn.commit()
                    
            except Exception as e:
                continue
        
        conn.commit()
        print(f" Импортировано {ratings_imported} оценок")
        if skipped_no_book > 0:
            print(f"     Пропущено {skipped_no_book} оценок (книга не найдена)")
        
    except FileNotFoundError:
        print(" ratings.csv не найден!")
        sys.exit(1)
    
    # Статистика
    print("\n" + "="*50)
    print(" ИТОГИ ИМПОРТА:")
    print("="*50)
    cursor.execute("SELECT COUNT(*) FROM Book")
    print(f" Книг: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Users")
    print(f" Пользователей: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Ratings")
    print(f" Оценок: {cursor.fetchone()[0]}")
    cursor.execute("SELECT MIN(rating), MAX(rating), AVG(rating) FROM Ratings")
    min_r, max_r, avg_r = cursor.fetchone()
    print(f" Рейтинг: min={min_r}, max={max_r}, avg={avg_r:.2f}")
    print("="*50)
    
    cursor.close()
    conn.close()
    
    print("\n Импорт завершён успешно!")
    print(" Перезапустите ML-сервис:")
    print("   docker-compose restart ml-service")
    
except pymysql.err.OperationalError as e:
    print(f"\n Ошибка подключения к MySQL: {e}")

    
except Exception as e:
    print(f"\n Ошибка: {e}")
    import traceback
    traceback.print_exc()