@extends('layouts.app')

@section('title', 'BookMania - Главная')

@section('content')
<!-- Hero Section -->
<div class="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 mb-8 text-white shadow-lg">
    <h1 class="text-4xl font-bold mb-4">Книжный Советник</h1>
    <p class="text-lg opacity-90 mb-6">Персональные рекомендации книг на основе ваших предпочтений</p>
    
    @auth
        <a href="{{ route('recommendations.index') }}" class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 inline-block transition">
            Мои рекомендации
        </a>
    @else
        <a href="{{ route('register') }}" class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 inline-block transition">
            Зарегистрироваться
        </a>
    @endauth
</div>

<!-- Popular Books -->
<h2 class="text-3xl font-bold mb-6 text-gray-800">Популярные книги</h2>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    @foreach($books as $book)
    <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition duration-300 transform hover:-translate-y-1">
        <!-- Book Cover -->
        <div class="h-64 bg-gradient-to-br from-gray-200 to-gray-300 overflow-hidden flex items-center justify-center">
            @if($book->image_url && $book->image_url != '/images/no-cover.jpg')
                <img src="{{ $book->image_url }}" alt="{{ $book->title }}" class="w-full h-full object-cover">
            @else
                <div class="text-center p-4">
                    <svg class="w-16 h-16 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                    </svg>
                    <p class="text-sm text-gray-500">Нет обложки</p>
                </div>
            @endif
        </div>
        
        <!-- Book Info -->
        <div class="p-5">
            <h3 class="text-lg font-bold mb-2 text-gray-800 line-clamp-2">{{ $book->title }}</h3>
            <p class="text-gray-600 text-sm mb-2">{{ $book->author }}</p>
            
            @if($book->year_publication)
            <p class="text-xs text-gray-500 mb-3">Год: {{ $book->year_publication }}</p>
            @endif
            
            <a href="{{ route('books.show', $book->book_id) }}" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm">
                Подробнее →
            </a>
        </div>
    </div>
    @endforeach
</div>

<!-- Catalog Link -->
<div class="mt-12 text-center">
    <a href="{{ route('books.index') }}" class="bg-gray-800 text-white px-8 py-3 rounded-lg hover:bg-gray-900 inline-block transition">
        Смотреть весь каталог
    </a>
</div>
@endsection