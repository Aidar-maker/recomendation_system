@extends('layouts.app')

@section('title', $book->title)

@section('content')
<div class="min-h-screen bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Хлебные крошки -->
        <nav class="text-sm text-gray-500 mb-6">
            <a href="{{ route('books.index') }}" class="hover:text-indigo-600">Каталог</a>
            <span class="mx-2">/</span>
            <span class="text-gray-800">{{ $book->title }}</span>
        </nav>

        <div class="flex gap-8">
            <!-- Левая колонка -->
            <div class="w-80 flex-shrink-0">
                <!-- Обложка -->
                <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-4">
                    <div class="aspect-[2/3] bg-gray-100 flex items-center justify-center">
                        @if($book->image_url && file_exists(public_path($book->image_url)))
                            <img src="{{ asset($book->image_url) }}" alt="{{ $book->title }}" class="w-full h-full object-cover">
                        @else
                            <svg class="w-20 h-20 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                        @endif
                    </div>
                </div>
                
                <!-- Кнопка избранного -->
                <button class="w-full bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-lg mb-4 hover:border-indigo-500 hover:text-indigo-600 transition flex items-center justify-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                    </svg>
                    Добавить в избранное
                </button>

                <!-- Дополнительная информация -->
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Дополнительная информация</h3>
                    
                    <div class="space-y-2 text-sm">
                        @if($book->publisher)
                        <div>
                            <span class="text-gray-500 block">Издатель</span>
                            <span class="text-gray-800">{{ $book->publisher }}</span>
                        </div>
                        @endif
                        
                        @if($book->isbn)
                        <div>
                            <span class="text-gray-500 block">ISBN</span>
                            <span class="text-gray-800">{{ $book->isbn }}</span>
                        </div>
                        @endif
                        
                        @if($book->year_publication)
                        <div>
                            <span class="text-gray-500 block">Год издания</span>
                            <span class="text-gray-800">{{ $book->year_publication }}</span>
                        </div>
                        @endif
                    </div>
                </div>

                <!-- Блок оценки -->
                @auth
                <div class="bg-white rounded-lg shadow p-4 mt-4">
                    @if($userRating)
                        <div class="text-center">
                            <span class="text-gray-500 text-sm">Ваша оценка</span>
                            <div class="text-2xl font-bold text-indigo-600 mt-1">{{ $userRating->rating }}<span class="text-base text-gray-400">/10</span></div>
                        </div>
                    @else
                        <h3 class="font-semibold text-gray-800 mb-2 text-sm">Оцените книгу</h3>
                        <form action="{{ route('books.rate', $book->book_id) }}" method="POST">
                            @csrf
                            <select name="rating" class="w-full border-gray-300 rounded-md text-sm mb-2">
                                <option value="">Выберите оценку</option>
                                @for($i = 1; $i <= 10; $i++)
                                    <option value="{{ $i }}">{{ $i }}</option>
                                @endfor
                            </select>
                            <button type="submit" class="w-full bg-indigo-600 text-white py-1.5 rounded-md hover:bg-indigo-700 transition text-sm font-medium">
                                Оценить
                            </button>
                        </form>
                    @endif
                </div>
                @endauth
            </div>

            <!-- Правая колонка -->
            <div class="flex-1">
                <!-- Заголовок и описание -->
                <div class="mb-8">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ $book->title }}</h1>
                    <p class="text-lg text-gray-600 mb-4">{{ $book->author }}</p>
                    
                    @if($averageRating > 0)
                    <div class="flex items-center gap-2 mb-4">
                        <svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                        <span class="text-gray-700">{{ number_format($averageRating, 1) }} из 10</span>
                    </div>
                    @endif

                    <div class="border-t border-gray-200 pt-4">
                        @if($book->description)
                        <p class="text-gray-700 leading-relaxed">{{ $book->description }}</p>
                        @endif
                    </div>
                </div>

                <!-- Похожие книги -->
                <div>
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Похожее на то что вы читали</h2>
                    <div class="grid grid-cols-5 gap-4">
                        @for($i = 1; $i <= 5; $i++)
                        <div class="bg-white rounded-lg shadow p-3 hover:shadow-md transition cursor-pointer">
                            <div class="aspect-[2/3] bg-gray-100 rounded mb-2 flex items-center justify-center">
                                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                            </div>
                            <p class="font-medium text-gray-900 text-xs truncate">Похожая книга {{ $i }}</p>
                            <p class="text-gray-500 text-xs">Автор</p>
                        </div>
                        @endfor
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection