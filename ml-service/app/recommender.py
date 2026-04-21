import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from .database import get_db_connection

class RecommendationEngine:
    """
    Движок рекомендаций (ОПТИМИЗИРОВАННЫЙ)
    """
    
    def __init__(self):
        self.conn = get_db_connection()
        self.ratings_df = None
        self.book_data = None
        
    def load_data(self):
        """Загружает данные из БД"""
        ratings_query = "SELECT user_id, book_id, rating FROM Ratings WHERE rating IS NOT NULL"
        self.ratings_df = pd.read_sql(ratings_query, self.conn)
        
        books_query = "SELECT book_id, title, author FROM Book"
        self.book_data = pd.read_sql(books_query, self.conn)
    
    def _create_user_item_matrix(self):
        """
        Создаёт матрицу пользователь × книга
        СИЛЬНО фильтруем для уменьшения размера
        """
        if self.ratings_df.empty:
            return None, None, None
        
        # Фильтр 1: Пользователи с >= 10 оценками (было 5)
        user_counts = self.ratings_df['user_id'].value_counts()
        active_users = user_counts[user_counts >= 10].index.tolist()
        
        # Фильтр 2: Книги с >= 5 оценками
        book_counts = self.ratings_df['book_id'].value_counts()
        active_books = book_counts[book_counts >= 5].index.tolist()
        
        # Фильтруем
        filtered_ratings = self.ratings_df[
            (self.ratings_df['user_id'].isin(active_users)) &
            (self.ratings_df['book_id'].isin(active_books))
        ]
        
        print(f"📊 Матрица: {len(active_users)} пользователей × {len(active_books)} книг")
        
        if filtered_ratings.empty:
            return None, None, None
        
        # Pivot таблица
        matrix = filtered_ratings.pivot_table(
            index='user_id', 
            columns='book_id', 
            values='rating',
            fill_value=0
        )
        
        return matrix, matrix.index.tolist(), matrix.columns.tolist()
    
    def get_user_recommendations(self, user_id: int, limit: int = 5):
        """
        Генерирует персональные рекомендации
        """
        self.load_data()
        
        if self.ratings_df.empty:
            return self._get_popular_books(limit)
        
        matrix, users, books = self._create_user_item_matrix()
        
        # Если матрица не создалась или пользователь не найден
        if matrix is None or user_id not in users:
            print(f"⚠️  Пользователь {user_id} не найден, возвращаем популярные")
            return self._get_popular_books(limit)
        
        # NMF с МЕНЬШИМ количеством компонентов
        n_components = min(10, len(users) - 1, len(books) - 1)
        print(f"🔧 NMF компонентов: {n_components}")
        
        try:
            model = NMF(n_components=n_components, random_state=42, init='random', max_iter=50)
            user_factors = model.fit_transform(matrix)
            item_factors = model.components_
            
            # Предсказание
            user_idx = users.index(user_id)
            predictions = np.dot(user_factors[user_idx], item_factors)
            
        except Exception as e:
            print(f"❌ NMF ошибка: {e}")
            return self._get_popular_books(limit)
        
        # Исключаем прочитанные
        rated_books = set(self.ratings_df[
            self.ratings_df['user_id'] == user_id
        ]['book_id'].values)
        
        # Формируем рекомендации
        recommendations = []
        for idx, book_id in enumerate(books):
            if book_id not in rated_books:
                recommendations.append({
                    'book_id': int(book_id),
                    'predicted_rating': round(float(predictions[idx]), 2)
                })
        
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
        top_recs = recommendations[:limit]
        
        # Добавляем информацию о книгах
        result = []
        for rec in top_recs:
            book_info = self.book_data[self.book_data['book_id'] == rec['book_id']]
            if not book_info.empty:
                result.append({
                    'book_id': rec['book_id'],
                    'title': book_info.iloc[0]['title'],
                    'author': book_info.iloc[0]['author'],
                    'predicted_rating': rec['predicted_rating']
                })
        
        print(f"✅ Найдено {len(result)} рекомендаций")
        return result
    
    def _get_popular_books(self, limit: int):
        """Возвращает популярные книги (fallback)"""
        query = """
            SELECT b.book_id, b.title, b.author, COUNT(r.rating) as cnt
            FROM Book b
            LEFT JOIN Ratings r ON b.book_id = r.book_id
            GROUP BY b.book_id
            ORDER BY cnt DESC
            LIMIT %s
        """
        df = pd.read_sql(query, self.conn, params=(limit,))
        df['predicted_rating'] = 4.5
        return df.to_dict('records')
    
    def get_similar_books(self, book_id: int, limit: int = 5):
        """Возвращает похожие книги через жанры"""
        query = """
            SELECT b2.book_id, b2.title, b2.author
            FROM Book b1
            JOIN Book_Genres bg1 ON b1.book_id = bg1.book_id
            JOIN Book_Genres bg2 ON bg1.genre_id = bg2.genre_id
            JOIN Book b2 ON bg2.book_id = b2.book_id
            WHERE b1.book_id = %s AND b2.book_id != %s
            GROUP BY b2.book_id
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        df = pd.read_sql(query, self.conn, params=(book_id, book_id, limit))
        return df.to_dict('records')