import pandas as pd

print("📚 Проверяем совпадение ISBN...")

# Загружаем книги (с пропуском битых строк)
books_df = pd.read_csv('data/books.csv', sep=';', encoding='latin-1', on_bad_lines='skip')
book_isbns = set(books_df['ISBN'].astype(str).str.strip())
print(f"Книг в books.csv: {len(book_isbns)}")

# Загружаем оценки
ratings_df = pd.read_csv('data/ratings.csv', sep=';', encoding='latin-1')
print(f"Оценок в ratings.csv: {len(ratings_df)}")

# Фильтруем оценки 6-10
high_ratings = ratings_df[ratings_df['Book-Rating'] >= 6]
print(f"Оценок 6-10: {len(high_ratings)}")

# Проверяем какие ISBN отсутствуют
rating_isbns = set(high_ratings['ISBN'].astype(str).str.strip())
missing_isbns = rating_isbns - book_isbns
print(f"ISBN из оценок 6-10: {len(rating_isbns)}")
print(f"Отсутствует в books.csv: {len(missing_isbns)}")
print(f"Совпадает: {len(rating_isbns & book_isbns)}")

# Проверяем оценки 1-5
low_ratings = ratings_df[(ratings_df['Book-Rating'] >= 1) & (ratings_df['Book-Rating'] <= 5)]
low_isbns = set(low_ratings['ISBN'].astype(str).str.strip())
print(f"\nОценок 1-5: {len(low_ratings)}")
print(f"ISBN из оценок 1-5: {len(low_isbns)}")
print(f"Совпадает с books.csv: {len(low_isbns & book_isbns)}")