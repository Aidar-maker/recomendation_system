<?php

use App\Http\Controllers\HomeController;
use App\Http\Controllers\BookController;
use App\Http\Controllers\RecommendationController;
use App\Http\Controllers\Auth\LoginController;
use Illuminate\Support\Facades\Route;

// Главная страница
Route::get('/', [HomeController::class, 'index'])->name('home');

// Маршруты для входа
Route::middleware(['guest'])->group(function () {
    Route::get('/login', [LoginController::class, 'showLoginForm'])->name('login');
    Route::post('/login', [LoginController::class, 'login']);
});

// Маршруты требующие авторизации
Route::middleware(['auth'])->group(function () {
    
    Route::post('/logout', [LoginController::class, 'logout'])->name('logout');
    // Книги
    Route::get('/books', [BookController::class, 'index'])->name('books.index');
    Route::get('/books/{id}', [BookController::class, 'show'])->name('books.show');
    Route::post('/books/{id}/rate', [BookController::class, 'rate'])->name('books.rate');
    
    // Рекомендации
    Route::get('/recommendations', [RecommendationController::class, 'index'])->name('recommendations.index');
    Route::post('/recommendations/genres', [RecommendationController::class, 'byGenres'])->name('recommendations.byGenres');
});

// Маршруты аутентификации (Breeze)
require __DIR__.'/auth.php';