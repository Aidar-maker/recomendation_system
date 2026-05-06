<?php

namespace App\Http\Controllers;

use App\Models\Book;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function index()
    {
        // Получаем несколько популярных книг для главной
        $books = Book::limit(6)->get();
        
        return view('home', compact('books'));
    }
}
