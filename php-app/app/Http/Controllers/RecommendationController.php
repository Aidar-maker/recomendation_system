<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class RecommendationController extends Controller
{
    // УБЕРИТЕ __construct отсюда!
    
    public function index()
    {
        // Проверяем авторизацию ПРЯМО В МЕТОДЕ
        if (!auth()->check()) {
            return redirect()->route('login')
                ->with('error', 'Пожалуйста, войдите в систему');
        }

        $userId = auth()->id();
        
        // Логирование для отладки
        Log::info('User ID: ' . $userId);
        
        // Если user_id null — выходим
        if (!$userId) {
            return redirect()->route('login')
                ->with('error', 'Пользователь не найден');
        }

        $mlServiceUrl = config('services.ml_service.url', 'http://ml-service:8000');
        $apiKey = config('services.ml_service.api_key', 'secret-ml-api-key-2024');

        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$apiKey}",
                'Content-Type' => 'application/json'
            ])->post("{$mlServiceUrl}/api/v1/recommend", [
                'user_id' => $userId,
                'limit' => 5
            ]);

            if ($response->successful()) {
                $recommendations = $response->json();
            } else {
                $recommendations = [];
                Log::error('ML API Error: ' . $response->status());
            }
        } catch (\Exception $e) {
            Log::error('ML API Exception: ' . $e->getMessage());
            $recommendations = [];
        }

        return view('recommendations.index', compact('recommendations'));
    }
}