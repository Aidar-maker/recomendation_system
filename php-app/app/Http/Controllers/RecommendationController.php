<?php

namespace App\Http\Controllers;

use App\Models\Book;
use App\Models\Genre;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class RecommendationController extends Controller
{
    // Персональные рекомендации
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
                'limit' => 10
            ]);

            if ($response->successful()) {
                $recommendations = $response->json();
                // Если ML вернул список book_id
                if (isset($recommendations['recommendations'])) {
                    $bookIds = $recommendations['recommendations'];
                    $books = Book::whereIn('book_id', $bookIds)->get();
                } else {
                    // Если вернул сразу книги
                    $books = collect($recommendations);
                }
            } else {
                // Если ML не ответил - покажем популярные
                $books = Book::inRandomOrder()->limit(10)->get();
            }
        } catch (\Exception $e) {
            Log::error('ML API Error: ' . $e->getMessage());
            // fallback - случайные книги
            $books = Book::inRandomOrder()->limit(10)->get();
        }

        return view('recommendations.index', compact('books'));
    }

    // Рекомендации по жанрам
    public function byGenres(Request $request)
    {
        $request->validate([
            'genres' => 'required|array|min:1',
            'limit' => 'integer|min:1|max:20'
        ]);

        $genreIds = $request->genres;
        $limit = $request->limit ?? 10;

        // Получаем книги выбранных жанров
        $books = Book::whereHas('genres', function($query) use ($genreIds) {
            $query->whereIn('genre_id', $genreIds);
        })
        ->inRandomOrder()
        ->limit($limit)
        ->get();

        return view('recommendations.index', compact('books'));
    }
}