<?php

namespace App\Http\Controllers;

use App\Models\Book;
use App\Models\Rating;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class BookController extends Controller
{
    public function index(Request $request)
    {
        $query = Book::query();
        
        if ($request->has('search')) {
            $search = $request->search;
            $query->where(function($q) use ($search) {
                $q->where('title', 'LIKE', "%{$search}%")
                  ->orWhere('author', 'LIKE', "%{$search}%");
            });
        }
        
        $books = $query->paginate(24);
        
        return view('books.index', compact('books'));
    }

    public function show($id)
    {
        $book = Book::findOrFail($id);
        $genres = $book->genres;
        
        $userRating = null;
        if (Auth::check()) {
            $userId = Auth::user()->user_id;
            
            $userRating = Rating::where('user_id', $userId)
                ->where('book_id', $id)
                ->first();
        }
        
        $averageRating = Rating::where('book_id', $id)->avg('rating');
        
        return view('books.show', compact('book', 'genres', 'userRating', 'averageRating'));
    }

    public function rate(Request $request, $bookId)
    {
        $request->validate([
            'rating' => 'required|integer|min:1|max:10'
        ]);

        if (!Auth::check()) {
            return redirect()->route('login')
                ->with('error', 'Пожалуйста, войдите в систему');
        }

        // Используем user_id из модели
        $userId = Auth::user()->user_id;

        Rating::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            [
                'rating' => $request->rating,
                'rated_at' => now()
            ]
        );

        return redirect()->back()->with('success', 'Оценка сохранена!');
    }
}