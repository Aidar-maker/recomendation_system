<?php

namespace App\Http\Controllers;

use App\Models\Book;
use App\Models\Rating;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class BookController extends Controller
{
    // Список всех книг с поиском
    public function index(Request $request)
    {
        $query = Book::query();
        
        // Поиск по названию или автору
        if ($request->has('search')) {
            $search = $request->search;
            $query->where(function($q) use ($search) {
                $q->where('title', 'LIKE', "%{$search}%")
                  ->orWhere('author', 'LIKE', "%{$search}%");
            });
        }
        
        $books = $query->paginate(20);
        
        return view('books.index', compact('books'));
    }

    // Карточка книги
    public function show($id)
    {
        $book = Book::findOrFail($id);
        $genres = $book->genres;
        
        return view('books.show', compact('book', 'genres'));
    }

    // Оценка книги
    public function rate(Request $request, $bookId)
    {
        $request->validate([
            'rating' => 'required|integer|min:1|max:10'
        ]);

        $userId = auth()->id();
        
        // Обновляем или создаём оценку
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