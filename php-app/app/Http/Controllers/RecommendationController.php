<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class RecommendationController extends Controller
{
    // Получение персональных рекомендаций
    public function index()
    {
        if (!Auth::check()) {
            return redirect()->route('login')
                ->with('error', 'Пожалуйста, войдите в систему');
        }

        $userId = Auth::id();
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

    // Рекомендации по жанрам (для новых пользователей)
    public function byGenres(Request $request)
    {
        $request->validate([
            'genres' => 'required|array|min:1',
            'limit' => 'integer|min:1|max:20'
        ]);

        $mlServiceUrl = config('services.ml_service.url', 'http://ml-service:8000');
        $apiKey = config('services.ml_service.api_key', 'secret-ml-api-key-2024');

        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$apiKey}",
                'Content-Type' => 'application/json'
            ])->post("{$mlServiceUrl}/api/v1/recommend/genres", [
                'genres' => $request->genres,
                'limit' => $request->limit ?? 5
            ]);

            if ($response->successful()) {
                $recommendations = $response->json();
            } else {
                $recommendations = [];
            }
        } catch (\Exception $e) {
            Log::error('ML API Exception: ' . $e->getMessage());
            $recommendations = [];
        }

        return view('recommendations.index', compact('recommendations'));
    }
}
