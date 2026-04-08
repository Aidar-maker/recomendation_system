# В начале файла замените импорт:
# from surprise import SVD, Dataset, Reader
# на:
from sklearn.decomposition import NMF
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from .database import get_db_connection

class RecommendationEngine:
    def __init__(self):
        self.conn = get_db_connection()
        self.user_item_matrix = None
        self.book_data = None
        
    def load_data(self):
        """Загрузка данных из БД"""
        ratings_query = "SELECT user_id, book_id, rating FROM Ratings WHERE rating IS NOT NULL"
        self.ratings_df = pd.read_sql(ratings_query, self.conn)
        
        books_query = "SELECT book_id, title, author FROM Book"
        self.book_data = pd.read_sql(books_query, self.conn)
        
    def _create_user_item_matrix(self):
        """Создание матрицы пользователь-книга"""
        if self.ratings_df.empty:
            return None, None, None
            
        # Pivot table: пользователи × книги
        matrix = self.ratings_df.pivot_table(
            index='user_id', 
            columns='book_id', 
            values='rating',
            fill_value=0
        )
        return matrix, matrix.index.tolist(), matrix.columns.tolist()
    
    def get_user_recommendations(self, user_id: int, limit: int = 5):
        """Персональные рекомендации через NMF"""
        self.load_data()
        
        if self.ratings_df.empty:
            return self._get_popular_books(limit)
        
        matrix, users, books = self._create_user_item_matrix()
        if matrix is None or user_id not in users:
            return self._get_popular_books(limit)
        
        # NMF для скрытых факторов
        model = NMF(n_components=20, random_state=42, init='random')
        user_factors = model.fit_transform(matrix)
        item_factors = model.components_
        
        # Прогноз для текущего пользователя
        user_idx = users.index(user_id)
        predictions = np.dot(user_factors[user_idx], item_factors)
        
        # Исключаем уже прочитанные книги
        rated_books = set(self.ratings_df[
            self.ratings_df['user_id'] == user_id
        ]['book_id'].values)
        
        recommendations = []
        for idx, book_id in enumerate(books):
            if book_id not in rated_books:
                recommendations.append({
                    'book_id': int(book_id),
                    'predicted_rating': round(float(predictions[idx]), 2)
                })
        
        # Сортировка и возврат топ-N
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
        
        return result
    
    def _get_popular_books(self, limit: int):
        """Fallback - популярные книги"""
        query = """
            SELECT b.book_id, b.title, b.author, COUNT(r.rating) as cnt
            FROM Book b
            LEFT JOIN Ratings r ON b.book_id = r.book_id
            GROUP BY b.book_id
            ORDER BY cnt DESC
            LIMIT %s
        """
        df = pd.read_sql(query, self.conn, params=(limit,))
        # Добавляем фиктивный рейтинг для совместимости
        df['predicted_rating'] = 4.5
        return df.to_dict('records')
    
    def get_similar_books(self, book_id: int, limit: int = 5):
        """Похожие книги (контентная фильтрация)"""
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