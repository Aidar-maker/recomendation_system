from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from sqlalchemy import text
import pandas as pd
from .recommender import RecommendationEngine
from .auth import (
    Token, UserCreate, UserLogin,
    get_password_hash, create_access_token, authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)
from jose import jwt
import time

app = FastAPI(title="Книжный Советник API", version="1.0.0")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === МОДЕЛИ ===

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
    check_query = "SELECT user_id FROM users WHERE email = %s"
    existing = pd.read_sql_query(check_query, conn, params=(user.email,))
    if not existing.empty:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    hashed_password = get_password_hash(user.password)
    insert_query = "INSERT INTO users (username, email, password_hash, age) VALUES (%s, %s, %s, %s)"
    conn.execute(insert_query, (user.username, user.email, hashed_password, user.age))
    conn.commit()
    
    result = conn.execute("SELECT LAST_INSERT_ID() as id")
    new_user_id = result.fetchone()[0]
    
    access_token = create_access_token(
        data={"sub": str(new_user_id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    from .database import get_db_connection
    conn = get_db_connection()
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
                "image_url": row['Image_url'],
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