from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from .recommender import RecommendationEngine
from .database import get_db_connection

app = FastAPI(title="Книжный Советник API", version="1.0.0")
security = HTTPBearer()

# Защита API ключом
API_KEY = "secret-ml-api-key-2024"

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = 5

class BookRecommendation(BaseModel):
    book_id: int
    title: str
    author: str
    predicted_rating: float

class SimilarBooksRequest(BaseModel):
    book_id: int
    limit: int = 5

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ml-recommender"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)