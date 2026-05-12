<?php

namespace App\Http\Controllers;

use App\Models\Book;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function index()
    {
        // Получаем 12 случайных книг для главной страницы
        $books = Book::inRandomOrder()->limit(12)->get();
        
        return view('home', compact('books'));
    }
}