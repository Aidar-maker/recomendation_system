from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from .recommender import RecommendationEngine

# Инициализация FastAPI приложения
app = FastAPI(title="Книжный Советник API", version="1.0.0")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API ключ для защиты от внешних запросов
API_KEY = "secret-ml-api-key-2024"

# Модель данных для запроса рекомендаций
class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = 5

# Модель данных для ответа
class BookRecommendation(BaseModel):
    book_id: int
    title: str
    author: str
    predicted_rating: float

# Модель для похожих книг
class SimilarBooksRequest(BaseModel):
    book_id: int
    limit: int = 5

# Проверка API ключа
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

# Эндпоинт проверки здоровья сервиса
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ml-recommender"}

# Эндпоинт получения рекомендаций
@app.post("/api/v1/recommend", response_model=List[BookRecommendation])
async def get_recommendations(
    request: RecommendationRequest,
    token: str = Depends(verify_token)
):
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_user_recommendations(request.user_id, request.limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинт похожих книг
@app.post("/api/v1/similar", response_model=List[BookRecommendation])
async def get_similar_books(
    request: SimilarBooksRequest,
    token: str = Depends(verify_token)
):
    try:
        engine = RecommendationEngine()
        similar = engine.get_similar_books(request.book_id, request.limit)
        return similar
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))