import pandas as pd

print("📊 Анализ ratings.csv...")
df = pd.read_csv('data/ratings.csv', sep=';', encoding='latin-1')

print("\nРаспределение оценок:")
print(df['Book-Rating'].value_counts().sort_index())

print(f"\nВсего оценок: {len(df)}")
print(f"Максимальная оценка: {df['Book-Rating'].max()}")
print(f"Минимальная оценка: {df['Book-Rating'].min()}")
print(f"Средняя оценка: {df['Book-Rating'].mean():.2f}")

print("\nОценок 10:", (df['Book-Rating'] == 10).sum())
print("Оценок 9:", (df['Book-Rating'] == 9).sum())
print("Оценок 8:", (df['Book-Rating'] == 8).sum())
print("Оценок 7:", (df['Book-Rating'] == 7).sum())
print("Оценок 6:", (df['Book-Rating'] == 6).sum())
print("Оценок 5:", (df['Book-Rating'] == 5).sum())
print("Оценок 0:", (df['Book-Rating'] == 0).sum())