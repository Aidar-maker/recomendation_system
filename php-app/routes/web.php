<?php

use App\Http\Controllers\HomeController;
use App\Http\Controllers\BookController;
use App\Http\Controllers\RecommendationController;
use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Auth;
use App\Models\User;  

// Главная страница с книгами
Route::get('/', [HomeController::class, 'index'])->name('home');

// Каталог книг
Route::get('/books', [BookController::class, 'index'])->name('books.index');
Route::get('/books/{id}', [BookController::class, 'show'])->name('books.show');
Route::post('/books/{id}/rate', [BookController::class, 'rate'])->name('books.rate');

// Рекомендации (требуют авторизации)
Route::middleware(['auth'])->group(function () {
    Route::get('/recommendations', [RecommendationController::class, 'index'])->name('recommendations.index');
    Route::post('/recommendations/genres', [RecommendationController::class, 'byGenres'])->name('recommendations.byGenres');
    Route::get('/profile', function () {
        return view('profile.edit', [
            'user' => Auth::user()
        ]);
    })->name('profile.edit');
});

// Убираем стандартный dashboard или перенаправляем на главную
Route::get('/dashboard', function () {
    return redirect()->route('home');
});

Route::get('/test-login', function() {
    $user = App\Models\User::where('login', 'testuser123')->first();
    
    if ($user) {
        Auth::login($user);
        return "Logged in as: " . Auth::user()->login;
    }
    
    return "User not found";
});

require __DIR__.'/auth.php';
