@extends('layouts.app')

@section('title', 'Каталог книг')

@section('content')
<div class="py-12">
    <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <!-- Заголовок и поиск -->
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-4">📚 Каталог книг</h1>
            
            <form method="GET" action="{{ route('books.index') }}" class="flex gap-4">
                <div class="flex-1">
                    <input 
                        type="text" 
                        name="search" 
                        value="{{ request('search') }}" 
                        placeholder="Поиск по названию или автору..."
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                </div>
                <button 
                    type="submit" 
                    class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                    🔍 Поиск
                </button>
                @if(request('search'))
                <a 
                    href="{{ route('books.index') }}" 
                    class="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
                >
                    ✕ Сбросить
                </a>
                @endif
            </form>
        </div>

        <!-- Счётчик -->
        <div class="mb-6 text-gray-600">
            Найдено книг: <span class="font-semibold">{{ $books->total() }}</span>
        </div>

        <!-- Сетка книг -->
        @if($books->count() > 0)
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            @foreach($books as $book)
            <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition duration-300">
                <!-- Обложка -->
                <div class="h-64 bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                    @if($book->image_url && file_exists(public_path($book->image_url)))
                        <img src="{{ asset($book->image_url) }}" alt="{{ $book->title }}" class="h-full w-full object-cover">
                    @else
                        <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                    @endif
                </div>
                
                <!-- Информация -->
                <div class="p-5">
                    <h3 class="text-lg font-bold mb-2 text-gray-800">{{ $book->title }}</h3>
                    <p class="text-gray-600 text-sm mb-2">{{ $book->author }}</p>
                    
                    @if($book->year_publication)
                    <p class="text-xs text-gray-500 mb-1">{{ $book->year_publication }}</p>
                    @endif
                    
                    @if($book->publisher)
                    <p class="text-xs text-gray-500 mb-3">{{ $book->publisher }}</p>
                    @endif
                    
                    <a href="{{ route('books.show', $book->book_id) }}" class="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition text-sm">
                        Подробнее →
                    </a>
                </div>
            </div>
            @endforeach
        </div>

        <!-- Пагинация -->
        <div class="mt-8">
            {{ $books->links() }}
        </div>
        @else
        <!-- Нет книг -->
        <div class="text-center py-12">
            <svg class="w-24 h-24 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
            </svg>
            <p class="text-gray-600 text-lg">Книги не найдены</p>
            @if(request('search'))
            <a href="{{ route('books.index') }}" class="text-indigo-600 hover:underline mt-2 inline-block">
                Показать все книги
            </a>
            @endif
        </div>
        @endif
    </div>
</div>
@endsection