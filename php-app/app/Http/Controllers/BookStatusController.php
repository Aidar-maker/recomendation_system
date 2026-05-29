<?php

namespace App\Http\Controllers;

use App\Models\Book;
use App\Models\UserBookStatus;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use DB;

class BookStatusController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth');
    }

    public function setStatus(Request $request, $bookId)
    {
        $request->validate([
            'status' => 'required|in:reading,completed,abandoned,planned,favorite'
        ]);

        $userId = Auth::user()->user_id;

        $status = UserBookStatus::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            ['status' => $request->status]
        );

        if ($request->ajax()) {
            return response()->json([
                'success' => true,
                'status' => $request->status,
                'message' => 'Статус книги обновлен'
            ]);
        }

        return back()->with('success', 'Статус книги обновлен');
    }

    public function setRating(Request $request, $bookId)
    {
        $request->validate([
            'rating' => 'required|integer|min:1|max:10'
        ]);

        $userId = Auth::user()->user_id;

        $status = UserBookStatus::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            ['rating' => $request->rating]
        );

        if ($request->ajax()) {
            return response()->json([
                'success' => true,
                'rating' => $request->rating,
                'message' => 'Оценка сохранена'
            ]);
        }

        return back()->with('success', 'Оценка сохранена');
    }

    public function setReview(Request $request, $bookId)
    {
        $request->validate([
            'review' => 'required|string|max:5000'
        ]);

        $userId = Auth::user()->user_id;

        $status = UserBookStatus::updateOrCreate(
            ['user_id' => $userId, 'book_id' => $bookId],
            ['review' => $request->review]
        );

        return back()->with('success', 'Рецензия сохранена');
    }

    public function myBooks()
    {
        $user = Auth::user();

        $statuses = [
            'reading' => collect(),
            'completed' => collect(),
            'abandoned' => collect(),
            'planned' => collect(),
            'favorite' => collect(),
        ];

        $userStatuses = UserBookStatus::where('user_id', $user->user_id)
            ->with('book')
            ->get();

        foreach ($userStatuses as $userStatus) {
            if ($userStatus->book) {
                $statuses[$userStatus->status]->push($userStatus->book);
            }
        }

        $counts = UserBookStatus::where('user_id', $user->user_id)
            ->select('status', DB::raw('count(*) as count'))
            ->groupBy('status')
            ->pluck('count', 'status');

        return view('books.my-books', compact('statuses', 'counts'));
    }

    public function getStatus($bookId)
    {
        $status = UserBookStatus::where('user_id', Auth::user()->user_id)
            ->where('book_id', $bookId)
            ->first();

        return response()->json([
            'status' => $status ? $status->status : null,
            'rating' => $status ? $status->rating : null,
            'review' => $status ? $status->review : null,
        ]);
    }
}