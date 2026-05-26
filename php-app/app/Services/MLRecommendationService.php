<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class MLRecommendationService
{
    protected $baseUrl;
    protected $apiKey;

    public function __construct()
    {
        $this->baseUrl = config('services.ml_api.url', 'http://ml-recommender:8000');
        $this->apiKey = config('services.ml_api.key', 'secret-ml-api-key-2024');
    }

    /**
     * Получить рекомендации для пользователя
     */
    public function getUserRecommendations(int $userId, int $limit = 10): array
    {
        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$this->apiKey}",
            ])->post("{$this->baseUrl}/api/v1/recommend", [
                'user_id' => $userId,
                'limit' => $limit,
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            Log::error('ML API error: ' . $response->body());
            return [];

        } catch (\Exception $e) {
            Log::error('ML API exception: ' . $e->getMessage());
            return $this->getFallbackRecommendations($limit);
        }
    }

    /**
     * Получить похожие книги
     */
    public function getSimilarBooks(int $bookId, int $limit = 5): array
    {
        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$this->apiKey}",
            ])->post("{$this->baseUrl}/api/v1/similar", [
                'book_id' => $bookId,
                'limit' => $limit,
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            return [];

        } catch (\Exception $e) {
            Log::error('ML API similar books error: ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Рекомендации по жанрам
     */
    public function getRecommendationsByGenres(array $genreIds, int $limit = 10): array
    {
        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$this->apiKey}",
            ])->post("{$this->baseUrl}/api/v1/recommend/genres", [
                'genres' => $genreIds,
                'limit' => $limit,
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            return [];

        } catch (\Exception $e) {
            Log::error('ML API genre recommendations error: ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Получить список жанров
     */
    public function getGenres(): array
    {
        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$this->apiKey}",
            ])->get("{$this->baseUrl}/api/v1/genres");

            if ($response->successful()) {
                return $response->json();
            }

            return [];

        } catch (\Exception $e) {
            Log::error('ML API genres error: ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Проверка здоровья ML сервиса
     */
    public function healthCheck(): bool
    {
        try {
            $response = Http::timeout(5)->get("{$this->baseUrl}/health");
            return $response->successful();
        } catch (\Exception $e) {
            return false;
        }
    }

    /**
     * Fallback рекомендации (популярные книги)
     */
    protected function getFallbackRecommendations(int $limit): array
    {
        $books = \App\Models\Book::withCount('ratings')
            ->orderBy('ratings_count', 'desc')
            ->limit($limit)
            ->get();

        return $books->map(function($book) {
            return [
                'book_id' => $book->book_id,
                'title' => $book->title,
                'author' => $book->author,
                'predicted_rating' => 4.5,
                'cover_url' => $book->image_url,
            ];
        })->toArray();
    }
}