from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from sqlalchemy import text
from jose import jwt
import pandas as pd
import os
import uuid
import io
import csv
import time
from .recommender import RecommendationEngine
from .models import Chapter, ReadingProgress, Book
from .auth import is_admin
from .auth import (
    Token, UserCreate, UserLogin,
    get_password_hash, create_access_token, authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)


app = FastAPI(title="Книжный Советник API", version="1.0.0")
security = HTTPBearer()

origins = [
    "http://localhost5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём папку для загрузок
UPLOAD_DIR = "uploads/covers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Раздаём статические файлы
app.mount("/static", StaticFiles(directory="."), name="static")

# === МОДЕЛИ ===
class UserStats(BaseModel):
    total_books: int
    books_read: int
    books_reading: int
    books_planned: int
    books_dropped: int
    average_rating: float

class UserChapterSubmissionCreate(BaseModel):
    book_id: int
    chapter_title: str
    chapter_content: str
    order_number: float
    chapter_id: Optional[int] = None
    is_edit: bool = False

class UserInfo(BaseModel):
    user_id: int
    username: str
    email: str
    role: str

class ChapterCreate(BaseModel):
    title: str
    content_html: str
    order_number: int

class BookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    year_publication: Optional[int] = None
    genre_ids: List[int] = []
    created_by: Optional[int] = None

class ProgressUpdate(BaseModel):
    chapter_id: int
    position_percent: float = 0.0

class ChapterResponse(BaseModel):
    chapter_id: int
    title: str
    order_number: float
    # content_html: str 

class BookDetailResponse(BaseModel):
    book_id: int
    title: str
    author: str
    description: Optional[str]
    image_url: Optional[str]
    chapters: List[ChapterResponse]

class RecommendationRequest(BaseModel):
    limit: int = 5

class BookRecommendation(BaseModel):
    book_id: int
    title: str
    author: str
    predicted_rating: float
    image_url: Optional[str] = None

class GenreItem(BaseModel):
    genre_id: int
    genre_name: str

class GenreRecommendationRequest(BaseModel):
    genres: List[int]
    limit: int = 5

class SimilarBooksRequest(BaseModel):
    book_id: int
    limit: int = 5

# === МОДЕЛИ ДЛЯ ПОЛЬЗОВАТЕЛЬСКИХ ЗАЯВОК ===

class UserBookSubmissionCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    year_publication: Optional[int] = None
    publisher: Optional[str] = None
    image_url: Optional[str] = None
    genre_ids: List[int] = []

class UserChapterSubmissionCreate(BaseModel):
    book_id: int
    chapter_title: str
    chapter_content: str
    order_number: float
    chapter_ip: Optional[str] = None
    is_edit: bool = False  

class SubmissionResponse(BaseModel):
    submission_id: int
    user_id: int
    title: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    created_at: Optional[str] = None


# === МОДЕЛИ ДЛЯ СПИСКОВ КНИГ ===

class BookWithDate(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: Optional[str]
    added_at: datetime

class BookWithStatus(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: Optional[str]
    status: int
    updated_at: datetime

class BookWithRating(BaseModel):
    book_id: int
    title: str
    author: str
    image_url: Optional[str]
    rating: int
    rated_at: datetime

class BooksListResponse(BaseModel):
    books: List[dict]
    total: int
    sort: str
    order: str

class RatingCreate(BaseModel):
    book_id: int
    rating: int = Field(..., ge=1, le=10)

class RatingUpdate(BaseModel):
    rating: int = Field(..., ge=1, le=10)

class StatusUpdate(BaseModel):
    status: int = Field(..., ge=1, le=4)

class BookGenresUpdate(BaseModel):
    genre_ids: List[int] = []

# === МОДЕЛИ ДЛЯ КАТАЛОГА ===

class BookListItem(BaseModel):
    book_id: int
    title: str
    author: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    year_publication: Optional[int] = None
    genres: List[dict] = []
    avg_rating: Optional[float] = None

class BooksCatalogResponse(BaseModel):
    books: List[BookListItem]
    total: int

# === МОДЕЛИ ДЛЯ МОДЕРАЦИИ ===

class ModerationRequestCreate(BaseModel):
    title: str
    description: str

class ModerationRequestResponse(BaseModel):
    request_id: int
    user_id: int
    title: str
    description: str
    status: str
    admin_note: Optional[str] = None
    created_at: Optional[str] = None

class ModerationDecision(BaseModel):
    status: str  # 'approved' или 'rejected'
    admin_note: Optional[str] = None

# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ===

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Проверяет токен и возвращает ID пользователя (int)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный токен: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ошибка: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ ===

@app.post("/api/v1/auth/register", response_model=Token)
async def register(user: UserCreate):
    from .database import get_db_connection
    
    conn = get_db_connection()
    
    try:
        # Проверка email (используем text() и именованные параметры)
        check_query = text("SELECT user_id FROM users WHERE email = :email")
        existing = pd.read_sql_query(check_query, conn, params={"email": user.email})
        
        if not existing.empty:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
        
        # Хеширование пароля
        hashed_password = get_password_hash(user.password)
        
        # Вставка пользователя (SQLAlchemy 2.0 синтаксис)
        insert_query = text("""
            INSERT INTO users (username, email, password_hash, age)
            VALUES (:username, :email, :password_hash, :age)
        """)
        
        conn.execute(insert_query, {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "age": user.age
        })
        conn.commit()
        
        # Получаем ID нового пользователя
        result = conn.execute(text("SELECT LAST_INSERT_ID() as id"))
        new_user_id = result.fetchone()[0]
        
        # Создаем токен
        access_token = create_access_token(
            data={"sub": str(new_user_id), "email": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    from .database import get_db_connection
    
    conn = get_db_connection()
    
    try:
        db_user = authenticate_user(conn, user.email, user.password)
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": str(db_user["user_id"]), "email": db_user["email"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ml-recommender"}

# === ЭНДПОИНТЫ РЕКОМЕНДАЦИЙ ===

@app.post("/api/v1/recommend", response_model=List[BookRecommendation])
async def get_recommendations(request: RecommendationRequest, user_id: int = Depends(get_current_user_id)):
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_user_recommendations(user_id, request.limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/genres", response_model=List[GenreItem])
async def get_genres(user_id: int = Depends(get_current_user_id)):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        query = "SELECT genre_id, genre_name FROM genres ORDER BY genre_name"
        df = pd.read_sql_query(query, conn)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommend/genres", response_model=List[BookRecommendation])
async def get_recommendations_by_genres(request: GenreRecommendationRequest, user_id: int = Depends(get_current_user_id)):
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_recommendations_by_genres(request.genres, request.limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/similar", response_model=List[BookRecommendation])
async def get_similar_books(request: SimilarBooksRequest, user_id: int = Depends(get_current_user_id)):
    try:
        engine = RecommendationEngine()
        similar = engine.get_similar_books(request.book_id, request.limit)
        return similar
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ЭНДПОИНТЫ ДЛЯ ИЗБРАННОГО ===

@app.get("/api/v1/favorites", response_model=BooksListResponse)
async def get_favorites(
    user_id: int = Depends(get_current_user_id),
    sort: Literal["date", "title", "rating"] = "date",
    order: Literal["asc", "desc"] = "desc"
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Определяем порядок сортировки
        sort_mapping = {
            "date": "f.added_at",
            "title": "b.title",
            "rating": "avg_rating"
        }
        sort_field = sort_mapping.get(sort, "f.added_at")
        order_direction = "ASC" if order == "asc" else "DESC"
        
        query = f"""
            SELECT b.book_id, b.title, b.author, b.image_url, 
                   f.added_at, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM favorites f
            JOIN books b ON f.book_id = b.book_id
            LEFT JOIN ratings r ON b.book_id = r.book_id
            WHERE f.user_id = %s
            GROUP BY b.book_id, b.title, b.author, b.image_url, f.added_at
            ORDER BY {sort_field} {order_direction}
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id,))
        
        if df.empty:
            return BooksListResponse(books=[], total=0, sort=sort, order=order)
        
        books = []
        for _, row in df.iterrows():
            books.append({
                "book_id": int(row['book_id']),
                "title": row['title'],
                "author": row['author'],
                "image_url": row['image_url'],
                "added_at": row['added_at'].isoformat() if pd.notna(row['added_at']) else None
            })
        
        return BooksListResponse(books=books, total=len(books), sort=sort, order=order)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/favorites/{book_id}")
async def add_to_favorites(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование книги
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check_book = pd.read_sql_query(check_query, conn, params={"book_id": book_id})
        if check_book.empty:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Добавляем в избранное
        query = text("""
            INSERT IGNORE INTO favorites (user_id, book_id)
            VALUES (:user_id, :book_id)
        """)
        conn.execute(query, {"user_id": user_id, "book_id": book_id})
        conn.commit()
        
        return {"message": "Книга добавлена в избранное", "book_id": book_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/v1/favorites/{book_id}")
async def remove_from_favorites(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = "DELETE FROM favorites WHERE user_id = %s AND book_id = %s"
        result = conn.execute(query, (user_id, book_id))
        conn.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Книга не найдена в избранном")
        
        return {"message": "Книга удалена из избранного", "book_id": book_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ЭНДПОИНТЫ ДЛЯ СТАТУСОВ ЧТЕНИЯ ===

@app.get("/api/v1/reading-statuses", response_model=BooksListResponse)
async def get_reading_statuses(
    user_id: int = Depends(get_current_user_id),
    status: Optional[int] = Query(None, ge=1, le=4),
    sort: Literal["date", "title", "rating"] = "date",
    order: Literal["asc", "desc"] = "desc"
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        sort_mapping = {
            "date": "rs.updated_at",
            "title": "b.title",
            "rating": "avg_rating"
        }
        sort_field = sort_mapping.get(sort, "rs.updated_at")
        order_direction = "ASC" if order == "asc" else "DESC"
        
        if status:
            query = f"""
                SELECT b.book_id, b.title, b.author, b.image_url,
                       rs.status, rs.updated_at, COALESCE(AVG(r.rating), 0) as avg_rating
                FROM reading_statuses rs
                JOIN books b ON rs.book_id = b.book_id
                LEFT JOIN ratings r ON b.book_id = r.book_id
                WHERE rs.user_id = %s AND rs.status = %s
                GROUP BY b.book_id, b.title, b.author, b.image_url, rs.status, rs.updated_at
                ORDER BY {sort_field} {order_direction}
            """
            df = pd.read_sql_query(query, conn, params=(user_id, status))
        else:
            query = f"""
                SELECT b.book_id, b.title, b.author, b.image_url,
                       rs.status, rs.updated_at, COALESCE(AVG(r.rating), 0) as avg_rating
                FROM reading_statuses rs
                JOIN books b ON rs.book_id = b.book_id
                LEFT JOIN ratings r ON b.book_id = r.book_id
                WHERE rs.user_id = %s
                GROUP BY b.book_id, b.title, b.author, b.image_url, rs.status, rs.updated_at
                ORDER BY {sort_field} {order_direction}
            """
            df = pd.read_sql_query(query, conn, params=(user_id,))
        
        if df.empty:
            return BooksListResponse(books=[], total=0, sort=sort, order=order)
        
        books = []
        for _, row in df.iterrows():
            books.append({
                "book_id": int(row['book_id']),
                "title": row['title'],
                "author": row['author'],
                "image_url": row['image_url'],
                "status": int(row['status']),
                "updated_at": row['updated_at'].isoformat() if pd.notna(row['updated_at']) else None
            })
        
        return BooksListResponse(books=books, total=len(books), sort=sort, order=order)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reading-statuses/{book_id}")
async def set_reading_status(
    book_id: int,
    status_data: StatusUpdate,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем книгу
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check_book = pd.read_sql_query(check_query, conn, params={"book_id": book_id})
        if check_book.empty:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Устанавливаем статус
        query = text("""
            INSERT INTO reading_statuses (user_id, book_id, status)
            VALUES (:user_id, :book_id, :status)
            ON DUPLICATE KEY UPDATE status = :status, updated_at = NOW()
        """)
        conn.execute(query, {
            "user_id": user_id, 
            "book_id": book_id, 
            "status": status_data.status
        })
        conn.commit()
        
        status_names = {1: "В планах", 2: "Читаю", 3: "Прочитано", 4: "Брошено"}
        return {
            "message": f"Статус установлен: {status_names[status_data.status]}",
            "book_id": book_id,
            "status": status_data.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/v1/reading-statuses/{book_id}")
async def remove_reading_status(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = "DELETE FROM reading_statuses WHERE user_id = %s AND book_id = %s"
        result = conn.execute(query, (user_id, book_id))
        conn.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Статус не найден")
        
        return {"message": "Статус удален", "book_id": book_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats/reading", response_model=UserStats)
async def get_reading_stats(user_id: int = Depends(get_current_user_id)):
    """Получить статистику чтения пользователя"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()

        # 1. Считаем книги по статусам
        status_query = text("""
            SELECT status, COUNT(*) as count
            FROM reading_statuses
            WHERE user_id = :user_id
            GROUP BY status
        """)
        status_df = pd.read_sql_query(status_query, conn, params={"user_id": user_id})

        stats = {
            "books_planned": 0,
            "books_reading": 0,
            "books_read": 0,
            "books_dropped": 0
        }
        
        # Маппинг статусов (1=В планах, 2=Читаю, 3=Прочитано, 4=Брошено)
        status_map = {1: "books_planned", 2: "books_reading", 3: "books_read", 4: "books_dropped"}
        
        if not status_df.empty:
            for _, row in status_df.iterrows():
                s = int(row['status'])
                if s in status_map:
                    stats[status_map[s]] = int(row['count'])

        total_books = sum(stats.values())

        # 2. Считаем средний рейтинг
        rating_query = text("SELECT AVG(rating) as avg_rating FROM ratings WHERE user_id = :user_id")
        rating_df = pd.read_sql_query(rating_query, conn, params={"user_id": user_id})
        
        avg_rating = 0.0
        if not rating_df.empty and pd.notna(rating_df.iloc[0]['avg_rating']):
            avg_rating = round(float(rating_df.iloc[0]['avg_rating']), 1)

        return {
            "total_books": total_books,
            "books_read": stats["books_read"],
            "books_reading": stats["books_reading"],
            "books_planned": stats["books_planned"],
            "books_dropped": stats["books_dropped"],
            "average_rating": avg_rating
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ЭНДПОИНТЫ ДЛЯ ОЦЕНОК ===

@app.get("/api/v1/my-ratings", response_model=BooksListResponse)
async def get_my_ratings(
    user_id: int = Depends(get_current_user_id),
    sort: Literal["date", "title", "rating"] = "date",
    order: Literal["asc", "desc"] = "desc"
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        sort_mapping = {
            "date": "r.rated_at",
            "title": "b.title",
            "rating": "r.rating"
        }
        sort_field = sort_mapping.get(sort, "r.rated_at")
        order_direction = "ASC" if order == "asc" else "DESC"
        
        query = f"""
            SELECT b.book_id, b.title, b.author, b.image_url,
                   r.rating, r.rated_at
            FROM ratings r
            JOIN books b ON r.book_id = b.book_id
            WHERE r.user_id = %s
            ORDER BY {sort_field} {order_direction}
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id,))
        
        if df.empty:
            return BooksListResponse(books=[], total=0, sort=sort, order=order)
        
        books = []
        for _, row in df.iterrows():
            books.append({
                "book_id": int(row['book_id']),
                "title": row['title'],
                "author": row['author'],
                "image_url": row['image_url'],
                "rating": int(row['rating']),
                "rated_at": row['rated_at'].isoformat() if pd.notna(row['rated_at']) else None
            })
        
        return BooksListResponse(books=books, total=len(books), sort=sort, order=order)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ratings")
async def create_or_update_rating(
    rating_data: RatingCreate,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем книгу
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check_book = pd.read_sql_query(check_query, conn, params={"book_id": rating_data.book_id})
        if check_book.empty:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Сохраняем оценку
        query = text("""
            INSERT INTO ratings (user_id, book_id, rating)
            VALUES (:user_id, :book_id, :rating)
            ON DUPLICATE KEY UPDATE rating = :rating, rated_at = NOW()
        """)
        conn.execute(query, {
            "user_id": user_id,
            "book_id": rating_data.book_id,
            "rating": rating_data.rating
        })
        conn.commit()
        
        return {
            "message": "Оценка сохранена",
            "book_id": rating_data.book_id,
            "rating": rating_data.rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/v1/ratings/{book_id}")
async def delete_rating(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = "DELETE FROM ratings WHERE user_id = %s AND book_id = %s"
        result = conn.execute(query, (user_id, book_id))
        conn.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        return {"message": "Оценка удалена", "book_id": book_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"⏱️ {request.method} {request.url.path} - {process_time:.3f}s")
    return response

@app.post("/api/v1/admin/books", response_model=BookDetailResponse)
async def create_book(
    book_data: BookCreate,
    user_id: int = Depends(get_current_user_id)
):
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            INSERT INTO books (title, author, description, image_url, year_publication, created_by)
            VALUES (:title, :author, :description, :image_url, :year_publication, :created_by)
        """)
        
        result = conn.execute(query, {
            "title": book_data.title,
            "author": book_data.author,
            "description": book_data.description,
            "image_url": book_data.image_url,
            "year_publication": book_data.year_publication,
            "created_by": book_data.created_by or user_id  # ← Сохраняем создателя
        })
        conn.commit()
        
        new_book_id = result.lastrowid
        
        # Добавляем жанры
        if book_data.genre_ids:
            for genre_id in book_data.genre_ids:
                insert_genre = text("""
                    INSERT INTO book_genre (book_id, genre_id)
                    VALUES (:book_id, :genre_id)
                """)
                conn.execute(insert_genre, {"book_id": new_book_id, "genre_id": genre_id})
            conn.commit()
        
        return {
            "book_id": new_book_id,
            "title": book_data.title,
            "author": book_data.author,
            "description": book_data.description,
            "image_url": book_data.image_url,
            "chapters": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/v1/admin/books/{book_id}/chapters", response_model=dict)
async def create_chapter(
    book_id: int,
    chapter_data: ChapterCreate,
    user_id: int = Depends(get_current_user_id)
):
    # Проверка прав админа
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование книги
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check = conn.execute(check_query, {"book_id": book_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Создаем главу
        query = text("""
            INSERT INTO chapters (book_id, title, content_html, order_number)
            VALUES (:book_id, :title, :content_html, :order_number)
        """)
        
        conn.execute(query, {
            "book_id": book_id,
            "title": chapter_data.title,
            "content_html": chapter_data.content_html,
            "order_number": chapter_data.order_number
        })
        conn.commit()
        
        return {"message": "Глава успешно добавлена", "book_id": book_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/books/{book_id}", response_model=BookDetailResponse)
async def get_book_detail(book_id: int):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Получаем книгу
        book_query = text("SELECT * FROM books WHERE book_id = :book_id")
        book_df = pd.read_sql_query(book_query, conn, params={"book_id": book_id})
        
        if book_df.empty:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        book = book_df.iloc[0]
        
        # Получаем главы
        chapters_query = text("""
            SELECT chapter_id, title, order_number 
            FROM chapters 
            WHERE book_id = :book_id 
            ORDER BY order_number ASC
        """)
        chapters_df = pd.read_sql_query(chapters_query, conn, params={"book_id": book_id})
        
        chapters = []
        if not chapters_df.empty:
            chapters = chapters_df.to_dict(orient='records')
        
        return {
            "book_id": int(book['book_id']),
            "title": book['title'],
            "author": book['author'],
            "description": book['description'],
            "image_url": book['image_url'],
            "chapters": chapters
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/books/{book_id}/chapters/{chapter_id}")
async def get_chapter_content(book_id: int, chapter_id: int):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT c.chapter_id, c.title, c.content_html, c.order_number,
                   (SELECT chapter_id FROM chapters WHERE book_id = :book_id AND order_number < c.order_number ORDER BY order_number DESC LIMIT 1) as prev_chapter_id,
                   (SELECT chapter_id FROM chapters WHERE book_id = :book_id AND order_number > c.order_number ORDER BY order_number ASC LIMIT 1) as next_chapter_id
            FROM chapters c
            WHERE c.chapter_id = :chapter_id AND c.book_id = :book_id
        """)
        
        df = pd.read_sql_query(query, conn, params={"book_id": book_id, "chapter_id": chapter_id})
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Глава не найдена")
        
        # Получаем ВСЕ главы книги для выпадающего списка
        all_chapters_query = text("""
            SELECT chapter_id, title, order_number
            FROM chapters
            WHERE book_id = :book_id
            ORDER BY order_number ASC
        """)
        
        all_chapters_df = pd.read_sql_query(all_chapters_query, conn, params={"book_id": book_id})
        all_chapters = []
        if not all_chapters_df.empty:
            for _, row in all_chapters_df.iterrows():
                # Форматируем номер главы: 0 -> "Глава 1", 0.5 -> "Глава 0.5", 1 -> "Глава 2"
                order_num = float(row['order_number'])
                if order_num == int(order_num):
                    display_num = int(order_num) + 1  # 0 -> 1, 1 -> 2 и т.д.
                else:
                    display_num = order_num
                
                all_chapters.append({
                    "chapter_id": int(row['chapter_id']),
                    "title": row['title'],
                    "order_number": order_num,
                    "display_name": f"Глава {display_num}"
                })
        
        row = df.iloc[0]
        return {
            "chapter_id": int(row['chapter_id']),
            "title": row['title'],
            "content_html": row['content_html'],
            "order_number": float(row['order_number']),
            "prev_chapter_id": int(row['prev_chapter_id']) if pd.notna(row['prev_chapter_id']) else None,
            "next_chapter_id": int(row['next_chapter_id']) if pd.notna(row['next_chapter_id']) else None,
            "all_chapters": all_chapters  # ← Добавили список всех глав
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# === ЭНДПОИНТЫ ДЛЯ ПРОГРЕССА ЧТЕНИЯ ===

@app.post("/api/v1/reading-progress", response_model=dict)
async def update_reading_progress(
    progress_data: ProgressUpdate,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем, существует ли прогресс
        check_query = text("""
            SELECT progress_id FROM reading_progress 
            WHERE user_id = :user_id AND book_id = (SELECT book_id FROM chapters WHERE chapter_id = :chapter_id)
        """)
        existing = conn.execute(check_query, {
            "user_id": user_id,
            "chapter_id": progress_data.chapter_id
        }).fetchone()
        
        if existing:
            # Обновляем
            update_query = text("""
                UPDATE reading_progress 
                SET chapter_id = :chapter_id, position_percent = :position_percent, last_read_at = NOW()
                WHERE user_id = :user_id AND book_id = (SELECT book_id FROM chapters WHERE chapter_id = :chapter_id)
            """)
            conn.execute(update_query, {
                "user_id": user_id,
                "chapter_id": progress_data.chapter_id,
                "position_percent": progress_data.position_percent
            })
        else:
            # Создаем новый
            insert_query = text("""
                INSERT INTO reading_progress (user_id, book_id, chapter_id, position_percent)
                VALUES (:user_id, (SELECT book_id FROM chapters WHERE chapter_id = :chapter_id), :chapter_id, :position_percent)
            """)
            conn.execute(insert_query, {
                "user_id": user_id,
                "chapter_id": progress_data.chapter_id,
                "position_percent": progress_data.position_percent
            })
        
        conn.commit()
        return {"message": "Прогресс сохранен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/reading-progress/{book_id}")
async def get_reading_progress(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT chapter_id, position_percent, last_read_at 
            FROM reading_progress 
            WHERE user_id = :user_id AND book_id = :book_id
        """)
        df = pd.read_sql_query(query, conn, params={"user_id": user_id, "book_id": book_id})
        
        if df.empty:
            return {"chapter_id": None, "position_percent": 0, "last_read_at": None}
        
        row = df.iloc[0]
        return {
            "chapter_id": int(row['chapter_id']) if pd.notna(row['chapter_id']) else None,
            "position_percent": float(row['position_percent']),
            "last_read_at": row['last_read_at']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# === ЭНДПОИНТ КАТАЛОГА ===

@app.get("/api/v1/books", response_model=BooksCatalogResponse)
async def get_books_catalog(
    genre_id: Optional[int] = None,
    search: Optional[str] = None,
    sort: str = "title",
    order: str = "asc",
    page: int = 1,
    per_page: int = 12
):
    """Получить список всех книг с фильтрацией, поиском, сортировкой и пагинацией"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Безопасная сортировка
        allowed_sorts = {
            "title": "b.title",
            "year": "b.year_publication",
            "rating": "avg_rating",
            "created_at": "b.created_at"
        }
        sort_column = allowed_sorts.get(sort, "b.title")
        order_direction = "DESC" if order.lower() == "desc" else "ASC"
        
        # Базовый запрос
        base_query = """
            SELECT 
                b.book_id, 
                b.title, 
                b.author, 
                b.description, 
                b.image_url,
                b.year_publication,
                b.created_at,
                COALESCE(AVG(r.rating), 0) as avg_rating
            FROM books b
            LEFT JOIN ratings r ON b.book_id = r.book_id
        """
        
        params = {}
        where_clauses = []
        
        # Фильтр по жанру
        if genre_id:
            base_query += " JOIN book_genre bg ON b.book_id = bg.book_id "
            where_clauses.append("bg.genre_id = :genre_id")
            params["genre_id"] = genre_id
        
        base_query += " WHERE 1=1 "
        
        # Поиск
        if search:
            where_clauses.append("(b.title LIKE :search OR b.author LIKE :search)")
            params["search"] = f"%{search}%"
        
        if where_clauses:
            base_query += " AND " + " AND ".join(where_clauses)
        
        # Группировка и сортировка
        base_query += f"""
            GROUP BY b.book_id, b.title, b.author, b.description, b.image_url, b.year_publication, b.created_at
            ORDER BY {sort_column} {order_direction}
        """
        
        # Получаем ВСЕ книги для подсчёта общего количества
        all_books_df = pd.read_sql_query(text(base_query), conn, params=params)
        total_books = len(all_books_df)
        
        # Применяем пагинацию
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        books_df = all_books_df.iloc[start_idx:end_idx]
        
        if books_df.empty:
            return BooksCatalogResponse(books=[], total=total_books)
        
        # Получаем жанры для книг на текущей странице
        book_ids = books_df['book_id'].tolist()
        placeholders = ','.join([f':id_{i}' for i in range(len(book_ids))])
        genres_params = {f'id_{i}': bid for i, bid in enumerate(book_ids)}

        # Получаем книги
        books_df = pd.read_sql_query(text(base_query), conn, params=params)
        
        if books_df.empty:
            return BooksCatalogResponse(books=[], total=0)
        
        # Получаем жанры для всех книг
        book_ids = books_df['book_id'].tolist()
        placeholders = ','.join([f':id_{i}' for i in range(len(book_ids))])
        genres_params = {f'id_{i}': bid for i, bid in enumerate(book_ids)}
        
        genres_query = text(f"""
            SELECT bg.book_id, g.genre_id, g.genre_name
            FROM book_genre bg
            JOIN genres g ON bg.genre_id = g.genre_id
            WHERE bg.book_id IN ({placeholders})
            ORDER BY g.genre_name
        """)
        
        genres_df = pd.read_sql_query(genres_query, conn, params=genres_params)
        
        # Группируем жанры по book_id
        genres_by_book = {}
        if not genres_df.empty:
            for _, row in genres_df.iterrows():
                bid = int(row['book_id'])
                if bid not in genres_by_book:
                    genres_by_book[bid] = []
                genres_by_book[bid].append({
                    'genre_id': int(row['genre_id']),
                    'genre_name': row['genre_name']
                })
        
        # Формируем ответ
        books = []
        for _, row in books_df.iterrows():
            book_id = int(row['book_id'])
            books.append({
                'book_id': book_id,
                'title': row['title'],
                'author': row['author'],
                'description': row['description'],
                'image_url': row['image_url'],
                'year_publication': int(row['year_publication']) if pd.notna(row['year_publication']) else None,
                'genres': genres_by_book.get(book_id, []),
                'avg_rating': round(float(row['avg_rating']), 1) if row['avg_rating'] > 0 else None
            })
        
        return BooksCatalogResponse(books=books, total=total_books)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === УДАЛЕНИЕ КНИГ И ГЛАВ ===

@app.delete("/api/v1/admin/books/{book_id}")
async def delete_book(
    book_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Удаление книги и всех её глав"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование книги
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check = conn.execute(check_query, {"book_id": book_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Удаляем книгу (каскадно удалятся главы через ON DELETE CASCADE)
        delete_query = text("DELETE FROM books WHERE book_id = :book_id")
        conn.execute(delete_query, {"book_id": book_id})
        conn.commit()
        
        return {"message": "Книга и все её главы удалены", "book_id": book_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/v1/admin/books/{book_id}/chapters/{chapter_id}")
async def delete_chapter(
    book_id: int,
    chapter_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Удаление конкретной главы"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование главы
        check_query = text("SELECT chapter_id FROM chapters WHERE chapter_id = :chapter_id AND book_id = :book_id")
        check = conn.execute(check_query, {"chapter_id": chapter_id, "book_id": book_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Глава не найдена")
        
        # Удаляем главу
        delete_query = text("DELETE FROM chapters WHERE chapter_id = :chapter_id")
        conn.execute(delete_query, {"chapter_id": chapter_id})
        conn.commit()
        
        return {"message": "Глава удалена", "chapter_id": chapter_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/v1/admin/upload-cover")
async def upload_cover(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    """Загрузка обложки книги"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    # Проверяем тип файла
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Допустимые форматы: JPEG, PNG, WebP")
    
    # Проверяем размер (макс 5 МБ)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс 5 МБ)")
    
    # Генерируем уникальное имя файла
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Возвращаем URL для доступа к файлу
    file_url = f"/static/{UPLOAD_DIR}/{unique_filename}"
    
    return {"url": file_url, "filename": unique_filename}

@app.get("/api/v1/library/export")
async def export_library(user_id: int = Depends(get_current_user_id)):
    """Экспорт библиотеки пользователя в CSV (только для админов)"""
    
    # Проверка прав администратора
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()

        # Получаем все книги пользователя из разных таблиц
        # Используем UNION для объединения данных
        query = text("""
            SELECT DISTINCT
                b.title,
                b.author,
                COALESCE(rs.status, 0) as status,
                COALESCE(r.rating, 0) as rating,
                COALESCE(f.added_at, b.created_at) as date_added
            FROM books b
            INNER JOIN (
                SELECT book_id FROM favorites WHERE user_id = :user_id
                UNION
                SELECT book_id FROM reading_statuses WHERE user_id = :user_id
                UNION
                SELECT book_id FROM ratings WHERE user_id = :user_id
            ) user_books ON b.book_id = user_books.book_id
            LEFT JOIN reading_statuses rs ON b.book_id = rs.book_id AND rs.user_id = :user_id
            LEFT JOIN ratings r ON b.book_id = r.book_id AND r.user_id = :user_id
            LEFT JOIN favorites f ON b.book_id = f.book_id AND f.user_id = :user_id
            ORDER BY date_added DESC
        """)
        
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        # Если библиотека пуста
        if df.empty:
            # Возвращаем CSV с заголовками но без данных
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            writer.writerow(['Название', 'Автор', 'Год', 'Статус', 'Оценка (1-10)', 'Дата добавления', 'Источник'])
            return Response(
                content=output.getvalue(),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=my_library.csv"}
            )

        # Маппинг статусов
        status_map = {0: "Не указано", 1: "В планах", 2: "Читаю", 3: "Прочитано", 4: "Брошено"}

        # Создаем CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Заголовки
        writer.writerow(['Название', 'Автор', 'Год', 'Статус', 'Оценка (1-10)', 'Дата добавления', 'Источник'])
        
        # Данные
        for _, row in df.iterrows():
            status_text = status_map.get(int(row['status']), "Не указано")
            rating_text = int(row['rating']) if row['rating'] > 0 else "—"
            year_text = int(row['year_publication']) if pd.notna(row['year_publication']) else "—"
            date_text = row['date_added'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['date_added']) else "—"
            
            writer.writerow([
                row['title'], 
                row['author'], 
                year_text, 
                status_text, 
                rating_text, 
                date_text,
                row['source']
            ])

        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=my_library.csv"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/admin/books/{book_id}/genres")
async def update_book_genres(
    book_id: int,
    genres_data: BookGenresUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """Обновить жанры книги"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование книги
        check_query = text("SELECT book_id FROM books WHERE book_id = :book_id")
        check = conn.execute(check_query, {"book_id": book_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Книга не найдена")
        
        # Удаляем старые жанры
        delete_query = text("DELETE FROM book_genre WHERE book_id = :book_id")
        conn.execute(delete_query, {"book_id": book_id})
        
        # Добавляем новые жанры
        if genres_data.genre_ids:
            for genre_id in genres_data.genre_ids:
                insert_query = text("""
                    INSERT INTO book_genre (book_id, genre_id)
                    VALUES (:book_id, :genre_id)
                """)
                conn.execute(insert_query, {"book_id": book_id, "genre_id": genre_id})
        
        conn.commit()
        
        return {"message": "Жанры обновлены", "book_id": book_id, "genre_ids": genres_data.genre_ids}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# === ЭНДПОИНТЫ ДЛЯ МОДЕРАЦИИ ===

@app.post("/api/v1/moderation/request", response_model=dict)
async def create_moderation_request(
    request_data: ModerationRequestCreate,
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь подаёт запрос на модерацию"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            INSERT INTO moderation_requests (user_id, title, description)
            VALUES (:user_id, :title, :description)
        """)
        
        result = conn.execute(query, {
            "user_id": user_id,
            "title": request_data.title,
            "description": request_data.description
        })
        conn.commit()
        
        return {
            "message": "Запрос отправлен на модерацию",
            "request_id": result.lastrowid
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/moderation/my-requests", response_model=List[ModerationRequestResponse])
async def get_my_moderation_requests(
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь видит свои запросы"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT request_id, user_id, title, description, status, admin_note, created_at
            FROM moderation_requests
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        if df.empty:
            return []
        
        requests = []
        for _, row in df.iterrows():
            requests.append({
                "request_id": int(row['request_id']),
                "user_id": int(row['user_id']),
                "title": row['title'],
                "description": row['description'],
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return requests
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/admin/moderation/requests", response_model=List[ModerationRequestResponse])
async def get_all_moderation_requests(
    status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    """Админ видит все запросы на модерацию"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = """
            SELECT mr.request_id, mr.user_id, u.username, u.email,
                   mr.title, mr.description, mr.status, mr.admin_note, mr.created_at
            FROM moderation_requests mr
            JOIN users u ON mr.user_id = u.user_id
        """
        
        params = {}
        if status:
            query += " WHERE mr.status = :status"
            params["status"] = status
        
        query += " ORDER BY mr.created_at DESC"
        
        df = pd.read_sql_query(text(query), conn, params=params)
        
        if df.empty:
            return []
        
        requests = []
        for _, row in df.iterrows():
            requests.append({
                "request_id": int(row['request_id']),
                "user_id": int(row['user_id']),
                "username": row['username'],
                "email": row['email'],
                "title": row['title'],
                "description": row['description'],
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return requests
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/v1/admin/moderation/{request_id}/decision")
async def moderate_request(
    request_id: int,
    decision: ModerationDecision,
    user_id: int = Depends(get_current_user_id)
):
    """Админ принимает решение по запросу"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен: нужны права администратора")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        # Проверяем существование запроса
        check_query = text("SELECT request_id FROM moderation_requests WHERE request_id = :request_id")
        check = conn.execute(check_query, {"request_id": request_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Запрос не найден")
        
        # Обновляем статус
        update_query = text("""
            UPDATE moderation_requests
            SET status = :status, admin_note = :admin_note
            WHERE request_id = :request_id
        """)
        
        conn.execute(update_query, {
            "request_id": request_id,
            "status": decision.status,
            "admin_note": decision.admin_note
        })
        conn.commit()
        
        return {"message": f"Запрос {decision.status}", "request_id": request_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/auth/me", response_model=UserInfo)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """Получить информацию о текущем пользователе"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("SELECT user_id, username, email, role FROM users WHERE user_id = :user_id")
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        row = df.iloc[0]
        return {
            "user_id": int(row['user_id']),
            "username": row['username'],
            "email": row['email'],
            "role": row['role']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# === ЭНДПОИНТЫ ДЛЯ ЗАЯВОК НА КНИГИ ===

@app.post("/api/v1/submissions/books", response_model=dict)
async def create_book_submission(
    submission: UserBookSubmissionCreate,
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь подаёт заявку на создание книги"""
    try:
        from .database import get_db_connection
        import json
        conn = get_db_connection()
        
        query = text("""
            INSERT INTO user_book_submissions 
            (user_id, title, author, description, year_publication, publisher, image_url, genre_ids)
            VALUES (:user_id, :title, :author, :description, :year_publication, :publisher, :image_url, :genre_ids)
        """)
        
        result = conn.execute(query, {
            "user_id": user_id,
            "title": submission.title,
            "author": submission.author,
            "description": submission.description,
            "year_publication": submission.year_publication,
            "publisher": submission.publisher,
            "image_url": submission.image_url,
            "genre_ids": json.dumps(submission.genre_ids)
        })
        conn.commit()
        
        return {
            "message": "Заявка на создание книги отправлена на модерацию",
            "submission_id": result.lastrowid
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/submissions/my-books", response_model=List[SubmissionResponse])
async def get_my_book_submissions(
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь видит свои заявки на книги"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT submission_id, user_id, title, status, admin_note, created_at
            FROM user_book_submissions
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        if df.empty:
            return []
        
        submissions = []
        for _, row in df.iterrows():
            submissions.append({
                "submission_id": int(row['submission_id']),
                "user_id": int(row['user_id']),
                "title": row['title'],
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return submissions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# === ЭНДПОИНТЫ ДЛЯ ЗАЯВОК НА ГЛАВЫ ===
@app.post("/api/v1/submissions/chapters", response_model=dict)
async def create_chapter_submission(
    submission: UserChapterSubmissionCreate,
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь подаёт заявку на добавление или редактирование главы"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        if submission.is_edit and submission.chapter_id:
            # РЕДАКТИРОВАНИЕ существующей главы
            check_query = text("""
                SELECT c.chapter_id, c.book_id, b.created_by 
                FROM chapters c
                JOIN books b ON c.book_id = b.book_id
                WHERE c.chapter_id = :chapter_id
            """)
            check = conn.execute(check_query, {
                "chapter_id": submission.chapter_id
            }).fetchone()
            
            if not check:
                raise HTTPException(status_code=404, detail="Глава не найдена")
            
            # Проверка прав
            if check.created_by != user_id:
                user_info_query = text("SELECT role FROM users WHERE user_id = :user_id")
                user_info = conn.execute(user_info_query, {"user_id": user_id}).fetchone()
                
                if not user_info or user_info.role != 'admin':
                    raise HTTPException(status_code=403, detail="Нет прав на редактирование этой главы")
            
            # Получаем текущие данные главы
            current_chapter_query = text("""
                SELECT title, content_html, order_number FROM chapters WHERE chapter_id = :chapter_id
            """)
            current = conn.execute(current_chapter_query, {
                "chapter_id": submission.chapter_id
            }).fetchone()
            
            query = text("""
                INSERT INTO user_chapter_submissions 
                (user_id, book_id, chapter_id, chapter_title, chapter_content, order_number, 
                 original_title, original_content, original_order_number)
                VALUES (:user_id, :book_id, :chapter_id, :chapter_title, :chapter_content, :order_number,
                        :orig_title, :orig_content, :orig_order)
            """)
            
            result = conn.execute(query, {
                "user_id": user_id,
                "book_id": check.book_id,
                "chapter_id": submission.chapter_id,
                "chapter_title": submission.chapter_title,
                "chapter_content": submission.chapter_content,
                "order_number": submission.order_number,
                "orig_title": current.title,
                "orig_content": current.content_html,
                "orig_order": float(current.order_number)
            })
            
        else:
            # СОЗДАНИЕ новой главы (старый код)
            check_query = text("""
                SELECT book_id, created_by FROM books WHERE book_id = :book_id
            """)
            check = conn.execute(check_query, {"book_id": submission.book_id}).fetchone()
            
            if not check:
                raise HTTPException(status_code=404, detail="Книга не найдена")
            
            if check.created_by != user_id:
                user_info_query = text("SELECT role FROM users WHERE user_id = :user_id")
                user_info = conn.execute(user_info_query, {"user_id": user_id}).fetchone()
                
                if not user_info or user_info.role != 'admin':
                    raise HTTPException(status_code=403, detail="Вы не можете добавлять главы к этой книге")
            
            query = text("""
                INSERT INTO user_chapter_submissions 
                (user_id, book_id, chapter_title, chapter_content, order_number)
                VALUES (:user_id, :book_id, :chapter_title, :chapter_content, :order_number)
            """)
            
            result = conn.execute(query, {
                "user_id": user_id,
                "book_id": submission.book_id,
                "chapter_title": submission.chapter_title,
                "chapter_content": submission.chapter_content,
                "order_number": submission.order_number
            })
        
        conn.commit()
        
        action = "редактирование" if submission.is_edit else "добавление"
        return {
            "message": f"Заявка на {action} главы отправлена на модерацию",
            "submission_id": result.lastrowid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/submissions/my-chapters", response_model=List[dict])
async def get_my_chapter_submissions(
    user_id: int = Depends(get_current_user_id)
):
    """Пользователь видит свои заявки на главы"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT cs.submission_id, cs.user_id, cs.book_id, b.title as book_title,
                   cs.chapter_title, cs.status, cs.admin_note, cs.created_at
            FROM user_chapter_submissions cs
            JOIN books b ON cs.book_id = b.book_id
            WHERE cs.user_id = :user_id
            ORDER BY cs.created_at DESC
        """)
        
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        if df.empty:
            return []
        
        submissions = []
        for _, row in df.iterrows():
            submissions.append({
                "submission_id": int(row['submission_id']),
                "user_id": int(row['user_id']),
                "book_id": int(row['book_id']),
                "book_title": row['book_title'],
                "chapter_title": row['chapter_title'],
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return submissions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# === АДМИНСКИЕ ЭНДПОИНТЫ ДЛЯ МОДЕРАЦИИ ===

@app.get("/api/v1/admin/submissions/books", response_model=List[dict])
async def get_all_book_submissions(
    status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    """Админ видит все заявки на книги"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        from .database import get_db_connection
        import json
        conn = get_db_connection()
        
        query = """
            SELECT s.submission_id, s.user_id, u.username, u.email,
                   s.title, s.author, s.description, s.year_publication,
                   s.publisher, s.image_url, s.genre_ids, s.status,
                   s.admin_note, s.created_at
            FROM user_book_submissions s
            JOIN users u ON s.user_id = u.user_id
        """
        
        params = {}
        if status:
            query += " WHERE s.status = :status"
            params["status"] = status
        
        query += " ORDER BY s.created_at DESC"
        
        df = pd.read_sql_query(text(query), conn, params=params)
        
        if df.empty:
            return []
        
        submissions = []
        for _, row in df.iterrows():
            submissions.append({
                "submission_id": int(row['submission_id']),
                "user_id": int(row['user_id']),
                "username": row['username'],
                "email": row['email'],
                "title": row['title'],
                "author": row['author'],
                "description": row['description'],
                "year_publication": int(row['year_publication']) if pd.notna(row['year_publication']) else None,
                "publisher": row['publisher'],
                "image_url": row['image_url'],
                "genre_ids": json.loads(row['genre_ids']) if pd.notna(row['genre_ids']) else [],
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return submissions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/v1/admin/submissions/books/{submission_id}/decision")
async def moderate_book_submission(
    submission_id: int,
    decision: dict,  # {"status": "approved"|"rejected", "admin_note": "..."}
    user_id: int = Depends(get_current_user_id)
):
    """Админ одобряет/отклоняет заявку на книгу"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        from .database import get_db_connection
        import json
        conn = get_db_connection()
        
        # Проверяем существование
        check_query = text("SELECT * FROM user_book_submissions WHERE submission_id = :id")
        check = conn.execute(check_query, {"id": submission_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        new_status = decision.get("status")
        admin_note = decision.get("admin_note")
        
        if new_status == "approved":
            # Создаём книгу
            book_query = text("""
                INSERT INTO books (title, author, description, year_publication, publisher, image_url, created_by)
                VALUES (:title, :author, :description, :year_publication, :publisher, :image_url, :created_by)
            """)

            book_result = conn.execute(book_query, {
                "title": check.title,
                "author": check.author,
                "description": check.description,
                "year_publication": check.year_publication,
                "publisher": check.publisher,
                "image_url": check.image_url,
                "created_by": check.user_id 
            })
            conn.commit()
            
            new_book_id = book_result.lastrowid
            
            # Добавляем жанры
            genre_ids = json.loads(check.genre_ids) if check.genre_ids else []
            for genre_id in genre_ids:
                genre_query = text("""
                    INSERT INTO book_genre (book_id, genre_id)
                    VALUES (:book_id, :genre_id)
                """)
                conn.execute(genre_query, {"book_id": new_book_id, "genre_id": genre_id})
            conn.commit()
        
        # Обновляем статус заявки
        update_query = text("""
            UPDATE user_book_submissions
            SET status = :status, admin_note = :admin_note
            WHERE submission_id = :submission_id
        """)
        
        conn.execute(update_query, {
            "submission_id": submission_id,
            "status": new_status,
            "admin_note": admin_note
        })
        conn.commit()
        
        return {
            "message": f"Заявка {new_status}",
            "submission_id": submission_id,
            "book_id": new_book_id if new_status == "approved" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/admin/submissions/chapters", response_model=List[dict])
async def get_all_chapter_submissions(
    status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    """Админ видит все заявки на главы"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = """
            SELECT cs.submission_id, cs.user_id, u.username, u.email,
                   cs.book_id, b.title as book_title,
                   cs.chapter_title, cs.chapter_content, cs.order_number,
                   cs.status, cs.admin_note, cs.created_at
            FROM user_chapter_submissions cs
            JOIN users u ON cs.user_id = u.user_id
            JOIN books b ON cs.book_id = b.book_id
        """
        
        params = {}
        if status:
            query += " WHERE cs.status = :status"
            params["status"] = status
        
        query += " ORDER BY cs.created_at DESC"
        
        df = pd.read_sql_query(text(query), conn, params=params)
        
        if df.empty:
            return []
        
        submissions = []
        for _, row in df.iterrows():
            submissions.append({
                "submission_id": int(row['submission_id']),
                "user_id": int(row['user_id']),
                "username": row['username'],
                "email": row['email'],
                "book_id": int(row['book_id']),
                "book_title": row['book_title'],
                "chapter_title": row['chapter_title'],
                "chapter_content": row['chapter_content'],
                "order_number": int(row['order_number']),
                "status": row['status'],
                "admin_note": row['admin_note'] if pd.notna(row['admin_note']) else None,
                "created_at": row['created_at'].isoformat() if pd.notna(row['created_at']) else None
            })
        
        return submissions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/v1/admin/submissions/chapters/{submission_id}/decision")
async def moderate_chapter_submission(
    submission_id: int,
    decision: dict,
    user_id: int = Depends(get_current_user_id)
):
    """Админ одобряет/отклоняет заявку на главу (создание или редактирование)"""
    if not is_admin(user_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        check_query = text("SELECT * FROM user_chapter_submissions WHERE submission_id = :id")
        check = conn.execute(check_query, {"id": submission_id}).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        new_status = decision.get("status")
        admin_note = decision.get("admin_note")
        
        if new_status == "approved":
            if check.chapter_id:  # Это РЕДАКТИРОВАНИЕ
                update_query = text("""
                    UPDATE chapters 
                    SET title = :title, content_html = :content, order_number = :order_number
                    WHERE chapter_id = :chapter_id
                """)
                
                conn.execute(update_query, {
                    "chapter_id": check.chapter_id,
                    "title": check.chapter_title,
                    "content": check.chapter_content,
                    "order_number": check.order_number
                })
                conn.commit()
            else:  # Это СОЗДАНИЕ
                chapter_query = text("""
                    INSERT INTO chapters (book_id, title, content_html, order_number)
                    VALUES (:book_id, :title, :content, :order_number)
                """)
                
                conn.execute(chapter_query, {
                    "book_id": check.book_id,
                    "title": check.chapter_title,
                    "content": check.chapter_content,
                    "order_number": check.order_number
                })
                conn.commit()
        
        # Обновляем статус
        update_query = text("""
            UPDATE user_chapter_submissions
            SET status = :status, admin_note = :admin_note
            WHERE submission_id = :submission_id
        """)
        
        conn.execute(update_query, {
            "submission_id": submission_id,
            "status": new_status,
            "admin_note": admin_note
        })
        conn.commit()
        
        return {
            "message": f"Заявка на главу {new_status}",
            "submission_id": submission_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/v1/my-books", response_model=List[dict])
async def get_my_books(
    user_id: int = Depends(get_current_user_id)
):
    """Получить книги, созданные текущим пользователем"""
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        
        query = text("""
            SELECT b.book_id, b.title, b.author, b.description, 
                   b.year_publication, b.publisher, b.image_url,
                   COUNT(DISTINCT c.chapter_id) as chapters_count
            FROM books b
            LEFT JOIN chapters c ON b.book_id = c.book_id
            WHERE b.created_by = :user_id
            GROUP BY b.book_id, b.title, b.author, b.description, 
                     b.year_publication, b.publisher, b.image_url
            ORDER BY b.created_at DESC
        """)
        
        df = pd.read_sql_query(query, conn, params={"user_id": user_id})
        
        if df.empty:
            return []
        
        books = []
        for _, row in df.iterrows():
            books.append({
                "book_id": int(row['book_id']),
                "title": row['title'],
                "author": row['author'],
                "description": row['description'],
                "year_publication": int(row['year_publication']) if pd.notna(row['year_publication']) else None,
                "publisher": row['publisher'],
                "image_url": row['image_url'],
                "chapters_count": int(row['chapters_count'])
            })
        
        return books
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()