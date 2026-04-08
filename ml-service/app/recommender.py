import pandas as pd
import numpy as np
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split
from .database import get_db_connection

class RecommendationEngine:
    def __init__(self):
        self.conn = get_db_connection()
        self.model = None
        self.book_data = None
        self.user_data = None
        
    def load_data(self):
        """Загрузка данных из БД"""
        ratings_query = "SELECT user_id, book_id, rating FROM Ratings WHERE rating IS NOT NULL"
        self.ratings_df = pd.read_sql(ratings_query, self.conn)
        
        books_query = "SELECT book_id, title, author FROM Book"
        self.book_data = pd.read_sql(books_query, self.conn)
        
    def train_model(self):
        """Обучение модели SVD"""
        if self.ratings_df.empty:
            return False
            
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(self.ratings_df[['user_id', 'book_id', 'rating']], reader)
        trainset, _ = train_test_split(data, test_size=0.2)
        
        self.model = SVD(n_epochs=25, verbose=False)
        self.model.fit(trainset)
        return True
    
    def get_user_recommendations(self, user_id: int, limit: int = 5):
        """Персональные рекомендации"""
        self.load_data()
        
        # Проверка истории пользователя
        user_ratings = self.ratings_df[self.ratings_df['user_id'] == user_id]
        
        if user_ratings.empty or self.ratings_df.empty:
            # Холодный старт - популярные книги
            return self._get_popular_books(limit)
        
        # Обучаем модель на лету (для продакшена лучше кэшировать)
        self.train_model()
        
        # Генерация прогнозов для непрочитанных книг
        rated_books = set(user_ratings['book_id'].values)
        all_books = set(self.book_data['book_id'].values)
        unread_books = list(all_books - rated_books)
        
        predictions = []
        for book_id in unread_books:
            pred = self.model.predict(user_id, book_id)
            predictions.append({
                'book_id': book_id,
                'predicted_rating': pred.est
            })
        
        # Сортировка и возврат топ-N
        predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)
        top_predictions = predictions[:limit]
        
        # Добавление информации о книгах
        result = []
        for pred in top_predictions:
            book_info = self.book_data[self.book_data['book_id'] == pred['book_id']]
            if not book_info.empty:
                result.append({
                    'book_id': int(pred['book_id']),
                    'title': book_info.iloc[0]['title'],
                    'author': book_info.iloc[0]['author'],
                    'predicted_rating': round(pred['predicted_rating'], 2)
                })
        
        return result
    
    def _get_popular_books(self, limit: int):
        """Fallback - популярные книги"""
        query = """
            SELECT b.book_id, b.title, b.author, COUNT(r.rating) as rating_count
            FROM Book b
            LEFT JOIN Ratings r ON b.book_id = r.book_id
            GROUP BY b.book_id
            ORDER BY rating_count DESC
            LIMIT %s
        """
        df = pd.read_sql(query, self.conn, params=(limit,))
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