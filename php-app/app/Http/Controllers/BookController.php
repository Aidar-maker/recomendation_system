<?php

namespace App\Http\Controllers;

use App\Models\Book;
use App\Models\UserBookStatus;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class BookController extends Controller
{
    public function index(Request $request)
    {
        $query = Book::query();
        
        if ($request->has('search') && $request->search) {
            $search = $request->search;
            $query->where(function($q) use ($search) {
                $q->where('title', 'like', "%{$search}%")
                  ->orWhere('author', 'like', "%{$search}%");
            });
        }
        
        $books = $query->paginate(24);
        
        return view('books.index', compact('books'));
    }
    
    public function show($id)
    {
        $book = Book::with('genres')->findOrFail($id);
        
        $averageRating = $book->ratings()->avg('rating');
        $averageRating = round($averageRating, 1);
        
        $userRating = null;
        $userStatus = null;
        
        if (Auth::check()) {
            $userRating = $book->ratings()->where('user_id', Auth::user()->user_id)->first();
            $userStatus = UserBookStatus::where('user_id', Auth::user()->user_id)
                ->where('book_id', $book->book_id)
                ->first();
        }
        
        return view('books.show', compact('book', 'averageRating', 'userRating', 'userStatus'));
    }
    
    public function rate(Request $request, $bookId)
    {
        $request->validate([
            'rating' => 'required|integer|min:1|max:10'
        ]);
        
        if (!Auth::check()) {
            return redirect()->route('login');
        }
        
        $userId = Auth::user()->user_id;
        
        $rating = \App\Models\Rating::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            ['rating' => $request->rating, 'rated_at' => now()]
        );
        
        // Также обновляем или создаем запись в user_book_status
        UserBookStatus::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            ['rating' => $request->rating]
        );
        
        return back()->with('success', 'Оценка сохранена');
    }
}