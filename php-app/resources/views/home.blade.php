@extends('layouts.app')

@section('title', 'BookMania - Главная')

@section('content')
<div class="py-12">
    <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 mb-8 text-white shadow-lg">
            <h1 class="text-4xl font-bold mb-4">BookMania</h1>
            <p class="text-lg opacity-90 mb-6">Персональные рекомендации книг</p>
            
            @auth
                <a href="{{ route('books.index') }}" class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 inline-block transition">
                    Смотреть каталог
                </a>
            @else
                <a href="{{ route('register') }}" class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 inline-block transition">
                    Зарегистрироваться
                </a>
            @endauth
        </div>

        <!-- Books Grid -->
        <h2 class="text-3xl font-bold mb-6 text-gray-800">Популярные книги</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            @foreach($books as $book)
            <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition duration-300">
                <div class="h-64 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                    <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                    </svg>
                </div>
                
                <div class="p-5">
                    <h3 class="text-lg font-bold mb-2 text-gray-800">{{ $book->title }}</h3>
                    <p class="text-gray-600 text-sm mb-2">{{ $book->author }}</p>
                    
                    @if($book->year_publication)
                    <p class="text-xs text-gray-500 mb-3">{{ $book->year_publication }}</p>
                    @endif
                    
                    <a href="{{ route('books.show', $book->book_id) }}" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm">
                        Подробнее →
                    </a>
                </div>
            </div>
            @endforeach
        </div>
    </div>
</div>
@endsection