# fast_check.py
import pandas as pd

print("⚡ Быстрая проверка...")

# Загружаем книги
books_df = pd.read_csv('data/books.csv', sep=';', encoding='latin-1', on_bad_lines='skip')
book_isbns = set(books_df['ISBN'].astype(str).str.strip())
print(f"📚 Книг: {len(book_isbns)}")

# Загружаем оценки
ratings_df = pd.read_csv('data/ratings.csv', sep=';', encoding='latin-1')

# Берём первые 10000 оценок 6-10
high_ratings = ratings_df[ratings_df['Book-Rating'] >= 6].head(10000)

# Проверяем
found = 0
for idx, row in high_ratings.iterrows():
    isbn = str(row['ISBN']).strip()
    if isbn in book_isbns:
        found += 1

print(f"✅ Из первых 10000 оценок 6-10: {found} найдено")
print(f"❌ Не найдено: {10000 - found}")
print(f"\n💡 Вывод: {'Книги есть' if found > 5000 else 'Книг мало в books.csv'}")