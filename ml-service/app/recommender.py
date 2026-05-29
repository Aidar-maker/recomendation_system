import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from .database import get_db_connection

class RecommendationEngine:
    """
    Движок рекомендаций с использованием SVD
    """
    
    def __init__(self):
        self.conn = get_db_connection()
        self.ratings_df = None
        self.book_data = None
        
    def load_data(self):
        """Загружает данные из БД"""
        ratings_query = "SELECT user_id, book_id, rating FROM Ratings WHERE rating IS NOT NULL"
        self.ratings_df = pd.read_sql_query(ratings_query, self.conn)
        
        books_query = "SELECT book_id, title, author, image_url FROM Book"
        self.book_data = pd.read_sql_query(books_query, self.conn)
    
    def _create_user_item_matrix(self):
        """Создаёт матрицу пользователь × книга"""
        if self.ratings_df.empty:
            return None, None, None
        
        user_counts = self.ratings_df['user_id'].value_counts()
        book_counts = self.ratings_df['book_id'].value_counts()
        
        active_users = user_counts[user_counts >= 2].index.tolist()
        active_books = book_counts[book_counts >= 2].index.tolist()
        
        if len(active_users) < 2 or len(active_books) < 2:
            return None, None, None
        
        filtered_ratings = self.ratings_df[
            (self.ratings_df['user_id'].isin(active_users)) &
            (self.ratings_df['book_id'].isin(active_books))
        ]
        
        if filtered_ratings.empty:
            return None, None, None
        
        try:
            matrix = filtered_ratings.pivot_table(
                index='user_id', 
                columns='book_id', 
                values='rating',
                fill_value=0
            )
            return matrix, matrix.index.tolist(), matrix.columns.tolist()
        except Exception as e:
            print(f"Ошибка создания матрицы: {e}")
            return None, None, None
    
    def get_user_recommendations(self, user_id: int, limit: int = 5):
        """Генерирует персональные рекомендации через SVD"""
        self.load_data()
        
        print(f"Запрос рекомендаций для user_id={user_id}")
        print(f"Всего оценок в БД: {len(self.ratings_df)}")
        
        rated_books = set(self.ratings_df[self.ratings_df['user_id'] == user_id]['book_id'].values)
        print(f"Пользователь оценил {len(rated_books)} книг")
        
        if len(self.ratings_df) < 50:
            print("Мало данных, возвращаем популярные книги")
            return self._get_popular_books(limit, exclude_ids=rated_books)
        
        matrix, users, books = self._create_user_item_matrix()
        
        if matrix is None or user_id not in users:
            print("Матрица не создана или пользователь не в матрице, возвращаем популярные")
            return self._get_popular_books(limit, exclude_ids=rated_books)
        
        # Центрируем матрицу (вычитаем среднее)
        matrix_mean = matrix.mean().mean()
        matrix_centered = matrix - matrix_mean
        
        # SVD с небольшим числом компонент
        n_components = min(5, matrix_centered.shape[0] - 1, matrix_centered.shape[1] - 1)
        if n_components < 1:
            n_components = 1
        
        print(f"SVD компонентов: {n_components}")
        
        try:
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            user_factors = svd.fit_transform(matrix_centered)
            item_factors = svd.components_
            
            user_idx = users.index(user_id)
            predictions = np.dot(user_factors[user_idx], item_factors) + matrix_mean
            
            print(f"Предсказания (min={predictions.min():.3f}, max={predictions.max():.3f})")
            
        except Exception as e:
            print(f"SVD ошибка: {e}")
            return self._get_popular_books(limit, exclude_ids=rated_books)
        
        # Формирование рекомендаций
        recommendations = []
        for idx, book_id in enumerate(books):
            if book_id not in rated_books:
                rating = predictions[idx]
                # Ограничиваем рейтинг в диапазоне 1-10
                rating = max(1, min(10, rating))
                recommendations.append({
                    'book_id': int(book_id),
                    'predicted_rating': round(rating, 1)
                })
        
        # Сортировка и выбор топ-N
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
        top_recs = recommendations[:limit]
        
        # Обогащение данными книг
        result = []
        for rec in top_recs:
            book_info = self.book_data[self.book_data['book_id'] == rec['book_id']]
            if not book_info.empty:
                result.append({
                    'book_id': rec['book_id'],
                    'title': book_info.iloc[0]['title'],
                    'author': book_info.iloc[0]['author'],
                    'predicted_rating': rec['predicted_rating'],
                    'cover_url': book_info.iloc[0].get('image_url', None)
                })
        
        # Если рекомендаций меньше limit, добиваем популярными
        if len(result) < limit:
            print(f"Мало рекомендаций ({len(result)}), добавляем популярные")
            needed = limit - len(result)
            pop_recs = self._get_popular_books(needed, exclude_ids=rated_books)
            result.extend(pop_recs)
        
        print(f"Возвращаем {len(result)} рекомендаций")
        return result
    
    def _get_popular_books(self, limit: int, exclude_ids=None):
        """Популярные книги"""
        if exclude_ids is None:
            exclude_ids = []
        
        exclude_tuple = tuple(exclude_ids) if exclude_ids else (0,)
        
        query = """
            SELECT b.book_id, b.title, b.author, 
                   COALESCE(ROUND(AVG(r.rating), 1), 7.5) as avg_rating
            FROM Book b
            LEFT JOIN Ratings r ON b.book_id = r.book_id
            WHERE b.book_id NOT IN %s
            GROUP BY b.book_id
            ORDER BY COUNT(r.rating) DESC, avg_rating DESC
            LIMIT %s
        """
        
        df = pd.read_sql_query(query, self.conn, params=(exclude_tuple, limit))
        
        if df.empty:
            query_all = """
                SELECT book_id, title, author, 7.5 as avg_rating
                FROM Book
                WHERE book_id NOT IN %s
                LIMIT %s
            """
            df = pd.read_sql_query(query_all, self.conn, params=(exclude_tuple, limit))
        
        df['predicted_rating'] = df['avg_rating']
        df['cover_url'] = None
        return df.to_dict('records')
    
    def get_similar_books(self, book_id: int, limit: int = 5):
        """Похожие книги через жанры"""
        query = """
            SELECT DISTINCT b2.book_id, b2.title, b2.author
            FROM Book b1
            JOIN Book_Genres bg1 ON b1.book_id = bg1.book_id
            JOIN Book_Genres bg2 ON bg1.genre_id = bg2.genre_id
            JOIN Book b2 ON bg2.book_id = b2.book_id
            WHERE b1.book_id = %s AND b2.book_id != %s
            GROUP BY b2.book_id, b2.title, b2.author
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, self.conn, params=(book_id, book_id, limit))
        df['predicted_rating'] = 7.5
        df['cover_url'] = None
        return df.to_dict('records')
    
    def get_content_based_recommendations(self, user_id: int, limit: int = 5):
        """Контентная фильтрация по жанрам"""
        query = """
            SELECT DISTINCT b.book_id, b.title, b.author
            FROM Book b
            JOIN Book_Genres bg ON b.book_id = bg.book_id
            JOIN User_Preferences up ON bg.genre_id = up.genre_id
            WHERE up.user_id = %s
            AND b.book_id NOT IN (SELECT book_id FROM Ratings WHERE user_id = %s)
            GROUP BY b.book_id, b.title, b.author
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, self.conn, params=(user_id, user_id, limit))
        if df.empty:
            return []
        df['predicted_rating'] = 7.5
        df['cover_url'] = None
        return df.to_dict('records')
    
    def get_recommendations_by_genres(self, genre_ids: list, limit: int = 5):
        """Рекомендации по жанрам"""
        if not genre_ids:
            return self._get_popular_books(limit)
        
        placeholders = ','.join(['%s'] * len(genre_ids))
        query = f"""
            SELECT DISTINCT b.book_id, b.title, b.author,
                   COUNT(DISTINCT bg.genre_id) as match_count
            FROM Book b
            JOIN Book_Genres bg ON b.book_id = bg.book_id
            WHERE bg.genre_id IN ({placeholders})
            GROUP BY b.book_id, b.title, b.author
            ORDER BY match_count DESC, b.title
            LIMIT %s
        """
        params = tuple(genre_ids) + (limit,)
        df = pd.read_sql_query(query, self.conn, params=params)
        if df.empty:
            return self._get_popular_books(limit)
        df['predicted_rating'] = 7.5
        df['cover_url'] = None
        return df.to_dict('records')