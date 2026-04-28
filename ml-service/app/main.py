from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from .recommender import RecommendationEngine

app = FastAPI(title="Книжный Советник API", version="1.0.0")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "secret-ml-api-key-2024"

class RecommendationRequest(BaseModel):
    user_id: int
    limit: int


class BookRecommendation(BaseModel):
    book_id: int
    title: str
    author: str
    predicted_rating: float
    cover_url: Optional[str] = None

class SimilarBooksRequest(BaseModel):
    book_id: int
    limit: int = 5

class GenreRecommendationRequest(BaseModel):
    genres: List[int]
    limit: int = 5

class GenreItem(BaseModel):
    genre_id: int
    genre_name: str

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ml-recommender"}

@app.post("/api/v1/recommend", response_model=List[BookRecommendation])
async def get_recommendations(request: RecommendationRequest, token: str = Depends(verify_token)):
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_user_recommendations(request.user_id, request.limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/genres", response_model=List[GenreItem])
async def get_genres(token: str = Depends(verify_token)):
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        query = "SELECT genre_id, genre_name FROM Genres ORDER BY genre_name"
        df = pd.read_sql_query(query, conn)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommend/genres", response_model=List[BookRecommendation])
async def get_recommendations_by_genres(request: GenreRecommendationRequest, token: str = Depends(verify_token)):
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_recommendations_by_genres(request.genres, request.limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/similar", response_model=List[BookRecommendation])
async def get_similar_books(request: SimilarBooksRequest, token: str = Depends(verify_token)):
    try:
        engine = RecommendationEngine()
        similar = engine.get_similar_books(request.book_id, request.limit)
        return similar
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))