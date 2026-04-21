import pandas as pd
import pymysql

conn = pymysql.connect(
    host='127.0.0.1',
    user='bookuser',
    password='bookpassword',
    database='book_recommender'
)

# Проверяем распределение
df = pd.read_sql("SELECT rating, COUNT(*) as count FROM Ratings GROUP BY rating ORDER BY rating", conn)
print("Распределение оценок в БД:")
print(df)

print(f"\nВсего оценок: {df['count'].sum()}")
print(f"Оценок >= 6: {df[df['rating'] >= 6]['count'].sum() if len(df[df['rating'] >= 6]) > 0 else 0}")

conn.close()