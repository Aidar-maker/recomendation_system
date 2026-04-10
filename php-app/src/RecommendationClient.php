<?php
namespace App;

/**
 * Клиент для общения с ML-сервисом (FastAPI)
 */
class RecommendationClient {
    private $apiUrl;
    private $apiKey;
    private $timeout = 1; // 1 секунда таймаут
    
    public function __construct() {
        // URL ML-сервиса из docker-compose
        $this->apiUrl = getenv('ML_SERVICE_URL') ?: 'http://ml-service:8000';
        $this->apiKey = getenv('ML_API_KEY') ?: 'secret-ml-api-key-2024';
    }
    
    /**
     * Получить рекомендации для пользователя
     */
    public function getRecommendations(int $userId, int $limit = 5): array {
        try {
            $url = "{$this->apiUrl}/api/v1/recommend";
            $data = json_encode(['user_id' => $userId, 'limit' => $limit]);
            
            $ch = curl_init($url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $this->apiKey
            ]);
            curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Если ML-сервис ответил успешно
            if ($httpCode === 200 && $response) {
                return json_decode($response, true);
            }
            
            // Fallback: популярные книги при ошибке
            return $this->getFallbackBooks($limit);
            
        } catch (\Exception $e) {
            error_log("ML Service Error: " . $e->getMessage());
            return $this->getFallbackBooks($limit);
        }
    }
    
    /**
     * Получить похожие книги
     */
    public function getSimilarBooks(int $bookId, int $limit = 5): array {
        try {
            $url = "{$this->apiUrl}/api/v1/similar";
            $data = json_encode(['book_id' => $bookId, 'limit' => $limit]);
            
            $ch = curl_init($url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $this->apiKey
            ]);
            curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            if ($httpCode === 200 && $response) {
                return json_decode($response, true);
            }
            
            return [];
            
        } catch (\Exception $e) {
            error_log("ML Service Error: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Заглушка при недоступности ML-сервиса
     */
    private function getFallbackBooks(int $limit): array {
        return [
            ['book_id' => 1, 'title' => 'Мастер и Маргарита', 'author' => 'Булгаков', 'predicted_rating' => 5.0],
            ['book_id' => 2, 'title' => 'Преступление и наказание', 'author' => 'Достоевский', 'predicted_rating' => 4.8],
        ];
    }
}