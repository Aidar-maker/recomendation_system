<?php
namespace App;

class RecommendationClient {
    private $apiUrl;
    private $apiKey;
    private $timeout = 1; // секунда
    
    public function __construct() {
        $this->apiUrl = getenv('ML_SERVICE_URL') ?: 'http://ml-service:8000';
        $this->apiKey = getenv('ML_API_KEY') ?: 'secret-ml-api-key-2024';
    }
    
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
            
            if ($httpCode === 200 && $response) {
                return json_decode($response, true);
            }
            
            return $this->getFallbackBooks($limit);
            
        } catch (\Exception $e) {
            error_log("ML Service Error: " . $e->getMessage());
            return $this->getFallbackBooks($limit);
        }
    }
    
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
    
    private function getFallbackBooks(int $limit): array {
        // Возвращает популярные книги при ошибке ML
        return [
            ['book_id' => 1, 'title' => 'Популярная книга 1', 'author' => 'Автор', 'predicted_rating' => 5.0],
            ['book_id' => 2, 'title' => 'Популярная книга 2', 'author' => 'Автор', 'predicted_rating' => 4.8],
        ];
    }
    
    public function logInteraction(int $userId, int $bookId, string $type): void {
        // Логирование в БД через основной PHP слой
        // Вызывается при просмотре, оценке, покупке
    }
}