@extends('layouts.app')

@section('title', 'Рекомендации для вас')

@section('content')
<div class="py-12">
    <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Рекомендации для вас</h1>
        <p class="text-gray-600 mb-8">Персональный подбор книг на основе ваших оценок</p>

        @if(count($books) > 0)
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            @foreach($books as $book)
            @php
                $rec = collect($recommendations)->firstWhere('book_id', $book->book_id);
                $rating = $rec['predicted_rating'] ?? 0;
            @endphp
            <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition duration-300">
                <div class="h-64 bg-gray-100 flex items-center justify-center">
                    <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                    </svg>
                </div>
                
                <div class="p-5">
                    <div class="text-sm text-gray-500 mb-2">Прогноз: {{ number_format($rating, 1) }}/10</div>
                    
                    <h3 class="text-lg font-bold mb-2 text-gray-800">{{ $book->title }}</h3>
                    <p class="text-gray-600 text-sm mb-3">{{ $book->author }}</p>
                    
                    <a href="{{ route('books.show', $book->book_id) }}" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm">
                        Подробнее
                    </a>
                </div>
            </div>
            @endforeach
        </div>
        @else
        <div class="text-center py-12">
            <p class="text-gray-600 text-lg">Пока нет рекомендаций. Оцените больше книг!</p>
            <a href="{{ route('books.index') }}" class="inline-block mt-4 text-indigo-600 hover:underline">
                Перейти в каталог
            </a>
        </div>
        @endif
    </div>
</div>
@endsection