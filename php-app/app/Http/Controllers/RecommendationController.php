<?php

namespace App\Http\Controllers;

use App\Services\MLRecommendationService;
use Illuminate\Support\Facades\Auth;

class RecommendationController extends Controller
{
    protected $mlService;

    public function __construct(MLRecommendationService $mlService)
    {
        $this->mlService = $mlService;
    }

    public function index()
    {
        $user = Auth::user();
        
        $recommendations = $this->mlService->getUserRecommendations($user->user_id, 12);

        $bookIds = array_column($recommendations, 'book_id');
        $books = \App\Models\Book::whereIn('book_id', $bookIds)
            ->get()
            ->sortBy(function($book) use ($bookIds) {
                return array_search($book->book_id, $bookIds);
            })
            ->values();

        return view('recommendations.index', compact('books', 'recommendations'));
    }
}