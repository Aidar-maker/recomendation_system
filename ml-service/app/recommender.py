import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from .database import get_db_connection
import time

class RecommendationEngine:
    """Движок рекомендаций с использованием SVD"""
    
    # кэширование
    _cache = {}           # Хранилище результатов
    _cache_time = {}      # Время сохранения кэша
    CACHE_TTL = 300       # Время жизни кэша: 300 секунд (5 минут)
    
    def __init__(self):
        self.conn = None
        
    def _get_conn(self):
        """Ленивое создание соединения с БД"""
        if self.conn is None:
            self.conn = get_db_connection()
        return self.conn
    
    def close(self):
        """Закрыть соединение с БД"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _get_cached_result(self, user_id, limit):
        """Получить результат из кэша, если он ещё актуален"""
        cache_key = f"user_{user_id}_limit_{limit}"
        
        if cache_key in self._cache:
            # Проверяем, не истёк ли срок жизни кэша
            if time.time() - self._cache_time[cache_key] < self.CACHE_TTL:
                print(f"[КЭШ] HIT для user_id={user_id}, limit={limit}")
                return self._cache[cache_key]
            else:
                print(f"[КЭШ] EXPIRED для user_id={user_id}")
                # Удаляем просроченный кэш
                del self._cache[cache_key]
                del self._cache_time[cache_key]
        
        print(f"[КЭШ] MISS для user_id={user_id}")
        return None
    
    def _set_cached_result(self, user_id, limit, result):
        """Сохранить результат в кэш"""
        cache_key = f"user_{user_id}_limit_{limit}"
        self._cache[cache_key] = result
        self._cache_time[cache_key] = time.time()
        print(f"[КЭШ] SAVE для user_id={user_id} (TTL: {self.CACHE_TTL}s)")
    
    def load_data(self):
        """Загружает данные из БД"""
        conn = self._get_conn()
        
        # ВСЕ имена таблиц в нижнем регистре!
        ratings_query = "SELECT user_id, book_id, rating FROM ratings WHERE rating IS NOT NULL"
        self.ratings_df = pd.read_sql_query(ratings_query, conn)
        
        books_query = "SELECT book_id, title, author, image_url FROM books"
        self.book_data = pd.read_sql_query(books_query, conn)
    
    def _create_user_item_matrix(self):
        """Создаёт матрицу пользователь × книга"""
        if self.ratings_df is None or self.ratings_df.empty:
            return None, None, None
        
        # Фильтруем пользователей и книги с достаточным количеством оценок
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
        
        # 1. Пытаемся получить из кэша
        cached = self._get_cached_result(user_id, limit)
        if cached is not None:
            return cached
        
        start_time = time.time()
        print(f"[START] Генерация рекомендаций для user_id={user_id}")
        
        try:
            self.load_data()
            
            # Если нет данных — возвращаем популярные
            if self.ratings_df is None or self.ratings_df.empty:
                print("Нет данных об оценках, возвращаем популярные")
                result = self._get_popular_books(limit)
                self._set_cached_result(user_id, limit, result)
                return result
            
            print(f"Всего оценок в БД: {len(self.ratings_df)}")
            
            # Книги, которые пользователь уже оценил (исключаем из рекомендаций)
            rated_books = set(self.ratings_df[self.ratings_df['user_id'] == user_id]['book_id'].values)
            print(f"Пользователь оценил {len(rated_books)} книг")
            
            # Если данных мало — возвращаем популярные (fallback)
            if len(self.ratings_df) < 10:
                print("Мало данных для SVD, возвращаем популярные")
                result = self._get_popular_books(limit, exclude_ids=rated_books)
                self._set_cached_result(user_id, limit, result)
                return result
            
            # Создаём матрицу
            matrix, users, books = self._create_user_item_matrix()
            
            if matrix is None or user_id not in users:
                print("Матрица не создана или пользователь не в матрице")
                result = self._get_popular_books(limit, exclude_ids=rated_books)
                self._set_cached_result(user_id, limit, result)
                return result
            
            # Центрируем матрицу (вычитаем среднее)
            matrix_mean = matrix.mean().mean()
            matrix_centered = matrix - matrix_mean
            
            # Выбираем количество компонент для SVD
            n_components = min(5, matrix_centered.shape[0] - 1, matrix_centered.shape[1] - 1)
            if n_components < 1:
                n_components = 1
            
            print(f"SVD компонентов: {n_components}")
            
            # Выполняем SVD
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            user_factors = svd.fit_transform(matrix_centered)
            item_factors = svd.components_
            
            # Предсказываем рейтинги для текущего пользователя
            user_idx = users.index(user_id)
            predictions = np.dot(user_factors[user_idx], item_factors) + matrix_mean
            
            print(f"📈 Предсказания (min={predictions.min():.3f}, max={predictions.max():.3f})")
            
            # Формируем список рекомендаций
            recommendations = []
            for idx, book_id in enumerate(books):
                if book_id not in rated_books:  # Пропускаем уже оценённые
                    rating = predictions[idx]
                    # Ограничиваем рейтинг диапазоном 1-10
                    rating = max(1, min(10, rating))
                    recommendations.append({
                        'book_id': int(book_id),
                        'predicted_rating': round(rating, 1)
                    })
            
            # Сортируем по предсказанному рейтингу и берём топ-N
            recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
            top_recs = recommendations[:limit]
            
            # Обогащаем рекомендации данными о книгах
            result = []
            for rec in top_recs:
                book_info = self.book_data[self.book_data['book_id'] == rec['book_id']]
                if not book_info.empty:
                    result.append({
                        'book_id': rec['book_id'],
                        'title': book_info.iloc[0]['title'],
                        'author': book_info.iloc[0]['author'],
                        'predicted_rating': rec['predicted_rating'],
                        'image_url': book_info.iloc[0].get('image_url', None)
                    })
            
            # Если рекомендаций меньше, чем нужно, добиваем популярными
            if len(result) < limit:
                print(f"➕ Мало рекомендаций ({len(result)}), добавляем популярные")
                needed = limit - len(result)
                pop_recs = self._get_popular_books(needed, exclude_ids=rated_books)
                result.extend(pop_recs)
            
            print(f"Возвращаем {len(result)} рекомендаций")
            
            # Кэшируем результат
            self._set_cached_result(user_id, limit, result)
            
            return result
            
        except Exception as e:
            print(f"Ошибка в get_user_recommendations: {e}")
            # В случае ошибки возвращаем популярные книги
            return self._get_popular_books(limit)
            
        finally:
            elapsed = time.time() - start_time
            print(f"[END] Запрос выполнен за {elapsed:.3f} секунд")
            self.close()  # Всегда закрываем соединение
    
    def _get_popular_books(self, limit: int, exclude_ids=None):
        """Популярные книги (fallback-метод)"""
        if exclude_ids is None:
            exclude_ids = []
        
        exclude_tuple = tuple(exclude_ids) if exclude_ids else (0,)
        conn = self._get_conn()
        
        # ВСЕ имена таблиц в нижнем регистре!
        query = """
            SELECT b.book_id, b.title, b.author, b.image_url,
                   COALESCE(ROUND(AVG(r.rating), 1), 7.5) as avg_rating
            FROM books b
            LEFT JOIN ratings r ON b.book_id = r.book_id
            WHERE b.book_id NOT IN %s
            GROUP BY b.book_id, b.title, b.author, b.image_url
            ORDER BY COUNT(r.rating) DESC, avg_rating DESC
            LIMIT %s
        """
        
        df = pd.read_sql_query(query, conn, params=(exclude_tuple, limit))
        
        # Фолбэк: если не получилось с рейтингами, берём просто книги
        if df.empty:
            query_all = """
                SELECT book_id, title, author, image_url, 7.5 as avg_rating
                FROM books
                WHERE book_id NOT IN %s
                LIMIT %s
            """
            df = pd.read_sql_query(query_all, conn, params=(exclude_tuple, limit))
        
        if not df.empty:
            df['predicted_rating'] = df['avg_rating']
        
        return df.to_dict('records')
    
    def get_similar_books(self, book_id: int, limit: int = 5):
        """Похожие книги через жанры"""
        try:
            conn = self._get_conn()
            
            # ВСЕ имена таблиц в нижнем регистре!
            query = """
                SELECT DISTINCT b2.book_id, b2.title, b2.author, b2.image_url
                FROM books b1
                JOIN book_genre bg1 ON b1.book_id = bg1.book_id
                JOIN book_genre bg2 ON bg1.genre_id = bg2.genre_id
                JOIN books b2 ON bg2.book_id = b2.book_id
                WHERE b1.book_id = %s AND b2.book_id != %s
                GROUP BY b2.book_id, b2.title, b2.author, b2.image_url
                ORDER BY COUNT(*) DESC
                LIMIT %s
            """
            df = pd.read_sql_query(query, conn, params=(book_id, book_id, limit))
            
            if not df.empty:
                df['predicted_rating'] = 7.5
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Ошибка в get_similar_books: {e}")
            return []
        finally:
            self.close()
    
    def get_recommendations_by_genres(self, genre_ids: list, limit: int = 5):
        """Рекомендации по жанрам"""
        if not genre_ids:
            return self._get_popular_books(limit)
        
        try:
            conn = self._get_conn()
            placeholders = ','.join(['%s'] * len(genre_ids))
            
            # ВСЕ имена таблиц в нижнем регистре!
            query = f"""
                SELECT DISTINCT b.book_id, b.title, b.author, b.image_url,
                       COUNT(DISTINCT bg.genre_id) as match_count
                FROM books b
                JOIN book_genre bg ON b.book_id = bg.book_id
                WHERE bg.genre_id IN ({placeholders})
                GROUP BY b.book_id, b.title, b.author, b.image_url
                ORDER BY match_count DESC, b.title
                LIMIT %s
            """
            params = tuple(genre_ids) + (limit,)
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['predicted_rating'] = 7.5
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Ошибка в get_recommendations_by_genres: {e}")
            return self._get_popular_books(limit)
        finally:
            self.close()