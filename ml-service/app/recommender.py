import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from .database import get_db_connection

class RecommendationEngine:
    """
    Движок рекомендаций
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
        active_users = user_counts[user_counts >= 10].index.tolist()
        
        book_counts = self.ratings_df['book_id'].value_counts()
        active_books = book_counts[book_counts >= 5].index.tolist()
        
        filtered_ratings = self.ratings_df[
            (self.ratings_df['user_id'].isin(active_users)) &
            (self.ratings_df['book_id'].isin(active_books))
        ]
        
        print(f"📊 Матрица: {len(active_users)} пользователей × {len(active_books)} книг")
        
        if filtered_ratings.empty:
            return None, None, None
        
        matrix = filtered_ratings.pivot_table(
            index='user_id', 
            columns='book_id', 
            values='rating',
            fill_value=0
        )
        
        return matrix, matrix.index.tolist(), matrix.columns.tolist()
    
    def get_user_recommendations(self, user_id: int, limit: int = 5):
        """Генерирует персональные рекомендации"""
        self.load_data()
        
        if self.ratings_df.empty:
            return self._get_popular_books(limit)
        
        matrix, users, books = self._create_user_item_matrix()
        
        if matrix is None or user_id not in users:
            print(f"⚠️  Пользователь {user_id} не найден, возвращаем популярные")
            return self._get_popular_books(limit)
        
        n_components = min(10, len(users) - 1, len(books) - 1)
        print(f"🔧 NMF компонентов: {n_components}")
        
        try:
            model = NMF(n_components=n_components, random_state=42, init='random', max_iter=50)
            user_factors = model.fit_transform(matrix)
            item_factors = model.components_
            
            user_idx = users.index(user_id)
            predictions = np.dot(user_factors[user_idx], item_factors)
            
        except Exception as e:
            print(f"NMF ошибка: {e}")
            return self._get_popular_books(limit)
        
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
        
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
        top_recs = recommendations[:limit]
        
        result = []
        for rec in top_recs:
            book_info = self.book_data[self.book_data['book_id'] == rec['book_id']]
            if not book_info.empty:
                book_result = {
                    'book_id': rec['book_id'],
                    'title': book_info.iloc[0]['title'],
                    'author': book_info.iloc[0]['author'],
                    'predicted_rating': rec['predicted_rating']
                }
                
                if 'image_url' in book_info.columns:
                    book_result['cover_url'] = book_info.iloc[0]['image_url']
                else:
                    book_result['cover_url'] = None
                
                result.append(book_result)
        
        if len(result) < limit:
            content_recs = self.get_content_based_recommendations(user_id, limit - len(result))
            result.extend(content_recs)
        
        print(f"Найдено {len(result)} рекомендаций")
        return result[:limit]
    
    def _get_popular_books(self, limit: int):
        """Возвращает популярные книги"""
        query = """
            SELECT b.book_id, b.title, b.author, COUNT(r.rating) as cnt
            FROM Book b
            LEFT JOIN Ratings r ON b.book_id = r.book_id
            GROUP BY b.book_id
            ORDER BY cnt DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        df['predicted_rating'] = 4.5
        df['cover_url'] = None
        return df.to_dict('records')
    
    def get_similar_books(self, book_id: int, limit: int = 5):
        """Возвращает похожие книги через жанры"""
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
        df['predicted_rating'] = 4.0
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
            AND b.book_id NOT IN (
                SELECT book_id FROM Ratings WHERE user_id = %s
            )
            GROUP BY b.book_id, b.title, b.author
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, self.conn, params=(user_id, user_id, limit))
        
        if df.empty:
            return []
        
        df['predicted_rating'] = 4.5
        df['cover_url'] = None
        return df.to_dict('records')
    
    def get_recommendations_by_genres(self, genre_ids: list, limit: int = 5):
        """
        Рекомендации по списку жанров (ИСПРАВЛЕНО!)
        """
        if not genre_ids:
            print("Нет жанров, возвращаем популярные")
            return self._get_popular_books(limit)
        
        try:
            # Создаем плейсхолдеры: %s,%s,%s
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
            
            print(f"Жанры: {genre_ids}")
            print(f"Параметры: {params}")
            
            df = pd.read_sql_query(query, self.conn, params=params)
            
            print(f"Найдено {len(df)} книг")
            
            if df.empty:
                print("⚠️  Книги не найдены")
                return self._get_popular_books(limit)
            
            df['predicted_rating'] = 4.0
            df['cover_url'] = None
            
            result = df.to_dict('records')
            print(f"Возвращаем {len(result)} рекомендаций")
            return result
            
        except Exception as e:
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return self._get_popular_books(limit)