@extends('layouts.app')

@section('title', $book->title . ' - BookMania')

@section('content')
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <!-- Left Column: Book Info -->
    <div class="lg:col-span-1">
        <div class="bg-white rounded-xl shadow-md p-6 sticky top-4">
            <!-- Cover -->
            <div class="aspect-[2/3] bg-gray-200 rounded-lg mb-6 overflow-hidden">
                @if($book->image_url)
                    <img src="{{ $book->image_url }}" alt="{{ $book->title }}" class="w-full h-full object-cover">
                @else
                    <div class="flex items-center justify-center h-full">
                        <svg class="w-20 h-20 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                    </div>
                @endif
            </div>

            <!-- Add to Favorites -->
            <button class="w-full border border-gray-300 rounded-lg py-3 mb-6 flex items-center justify-center space-x-2 hover:bg-gray-50">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                </svg>
                <span>Добавить в избранное</span>
            </button>

            <!-- Additional Info -->
            <div class="border-t pt-6">
                <h3 class="font-semibold mb-4">Дополнительная информация</h3>
                <dl class="space-y-3 text-sm">
                    @if($book->publisher)
                    <div>
                        <dt class="text-gray-500">Издатель</dt>
                        <dd class="font-medium">{{ $book->publisher }}</dd>
                    </div>
                    @endif
                    
                    @if($book->year_publication)
                    <div>
                        <dt class="text-gray-500">Год издания</dt>
                        <dd class="font-medium">{{ $book->year_publication }}</dd>
                    </div>
                    @endif
                    
                    @if($book->isbn)
                    <div>
                        <dt class="text-gray-500">ISBN</dt>
                        <dd class="font-medium">{{ $book->isbn }}</dd>
                    </div>
                    @endif
                </dl>
            </div>
        </div>
    </div>

    <!-- Right Column: Details & Recommendations -->
    <div class="lg:col-span-2">
        <!-- Book Details -->
        <div class="bg-white rounded-xl shadow-md p-8 mb-8">
            <h1 class="text-3xl font-bold mb-2">{{ $book->title }}</h1>
            <p class="text-xl text-gray-600 mb-6">{{ $book->author }}</p>
            
            <div class="prose max-w-none">
                <p class="text-gray-700 leading-relaxed">
                    <!-- Описание книги (если есть в БД) -->
                    Эпическая история о людях разума в мире, который рушится. 
                    <!-- Здесь можно добавить поле description в БД -->
                </p>
            </div>

            @if($genres->count() > 0)
            <div class="mt-6">
                <h3 class="font-semibold mb-3">Жанры:</h3>
                <div class="flex flex-wrap gap-2">
                    @foreach($genres as $genre)
                    <span class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm">
                        {{ $genre->genre_name }}
                    </span>
                    @endforeach
                </div>
            </div>
            @endif

            <!-- Rating Form -->
            @auth
            <div class="mt-8 border-t pt-6">
                <h3 class="text-xl font-semibold mb-4">Оценить книгу:</h3>
                <form action="{{ route('books.rate', $book->book_id) }}" method="POST">
                    @csrf
                    <div class="flex items-center gap-4">
                        <select name="rating" class="border rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500">
                            @for($i = 1; $i <= 10; $i++)
                            <option value="{{ $i }}" {{ ($userRating && $userRating->rating == $i) ? 'selected' : '' }}>
                                {{ $i }}
                            </option>
                            @endfor
                        </select>
                        <button type="submit" class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700">
                            Сохранить оценку
                        </button>
                    </div>
                </form>
                
                @if($userRating)
                <p class="mt-4 text-gray-600">Ваша оценка: <strong class="text-indigo-600">{{ $userRating->rating }}/10</strong></p>
                @endif
            </div>
            @else
            <div class="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p class="text-yellow-700">
                    <a href="{{ route('login') }}" class="font-medium underline">Войдите</a> 
                    чтобы оценить книгу и получить персональные рекомендации
                </p>
            </div>
            @endauth
        </div>

        <!-- Similar Books (Recommendations) -->
        <div class="bg-white rounded-xl shadow-md p-8">
            <h2 class="text-2xl font-bold mb-6">Похожее на то что вы читали</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <!-- Здесь будут рекомендации от ML-сервиса -->
                @for($i = 1; $i <= 5; $i++)
                <div class="bg-gray-50 rounded-lg p-4 text-center hover:shadow-md transition">
                    <div class="aspect-[2/3] bg-gray-200 rounded mb-3"></div>
                    <h4 class="font-medium text-sm mb-1">Книга {{ $i }}</h4>
                    <p class="text-xs text-gray-500">Автор</p>
                </div>
                @endfor
            </div>
        </div>
    </div>
</div>
@endsection