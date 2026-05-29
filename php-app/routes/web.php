<?php

use App\Http\Controllers\HomeController;
use App\Http\Controllers\BookController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\RecommendationController;
use App\Http\Controllers\BookStatusController;
use Illuminate\Support\Facades\Route;

// Главная страница
Route::get('/', [HomeController::class, 'index'])->name('home');

// Каталог книг
Route::get('/books', [BookController::class, 'index'])->name('books.index');
Route::get('/books/{id}', [BookController::class, 'show'])->name('books.show');
Route::post('/books/{id}/rate', [BookController::class, 'rate'])->name('books.rate');

// Профиль
Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
    Route::get('recommendations', [RecommendationController::class, 'index'])
        ->name('recommendations.index');
    Route::post('/books/{book}/status', [BookStatusController::class, 'setStatus'])->name('books.set-status');
    Route::post('/books/{book}/rating', [BookStatusController::class, 'setRating'])->name('books.set-rating');
    Route::post('/books/{book}/review', [BookStatusController::class, 'setReview'])->name('books.set-review');
    Route::get('/my-books', [BookStatusController::class, 'myBooks'])->name('my-books');
    Route::get('/books/{book}/status', [BookStatusController::class, 'getStatus'])->name('books.get-status');
});

require __DIR__.'/auth.php';