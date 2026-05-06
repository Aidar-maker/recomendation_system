<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@yield('title', 'BookMania')</title>
    
    <!-- Tailwind CSS через CDN (для быстрой разработки) -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- ИЛИ через Vite (для продакшена) -->
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <!-- Logo -->
                <div class="flex items-center">
                    <a href="{{ route('home') }}" class="flex items-center space-x-2">
                        <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                        <span class="text-xl font-bold text-gray-800">BookMania</span>
                    </a>
                </div>

                <!-- Search -->
                <div class="flex-1 max-w-lg mx-8">
                    <form action="{{ route('books.index') }}" method="GET" class="relative">
                        <input type="text" name="search" placeholder="Поиск книг, авторов..." 
                               class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <svg class="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </form>
                </div>

                <!-- Right Menu -->
                <div class="flex items-center space-x-6">
                    <a href="#" class="text-gray-600 hover:text-indigo-600 flex items-center space-x-1">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                        </svg>
                        <span>Избранное</span>
                    </a>
                    
                    @auth
                        <a href="{{ route('profile') }}" class="text-gray-600 hover:text-indigo-600 flex items-center space-x-1">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                            <span>Профиль</span>
                        </a>
                    @else
                        <a href="{{ route('login') }}" class="text-gray-600 hover:text-indigo-600">Войти</a>
                    @endauth
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        @yield('content')
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t mt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div>
                    <div class="flex items-center space-x-2 mb-4">
                        <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                        <span class="text-lg font-bold text-gray-800">BookMania</span>
                    </div>
                    <p class="text-gray-600 text-sm">Ваш надежный источник литературы. Тысячи книг на любой вкус.</p>
                </div>

                <div>
                    <h4 class="font-semibold mb-4">Быстрые ссылки</h4>
                    <ul class="space-y-2 text-sm text-gray-600">
                        <li><a href="{{ route('home') }}" class="hover:text-indigo-600">О нас</a></li>
                        <li><a href="{{ route('books.index') }}" class="hover:text-indigo-600">Каталог</a></li>
                        <li><a href="#" class="hover:text-indigo-600">Бестселлеры</a></li>
                    </ul>
                </div>

                <div>
                    <h4 class="font-semibold mb-4">Помощь</h4>
                    <ul class="space-y-2 text-sm text-gray-600">
                        <li><a href="#" class="hover:text-indigo-600">Оплата</a></li>
                        <li><a href="#" class="hover:text-indigo-600">Возврат</a></li>
                        <li><a href="#" class="hover:text-indigo-600">FAQ</a></li>
                    </ul>
                </div>

                <div>
                    <h4 class="font-semibold mb-4">Контакты</h4>
                    <ul class="space-y-2 text-sm text-gray-600">
                        <li>📧 info@bookmania.ru</li>
                        <li>📞 +7 (495) 123-45-67</li>
                        <li>📍 Югрск, ул. Пушкина, д. 10</li>
                    </ul>
                </div>
            </div>

            <div class="border-t mt-8 pt-8 text-center text-sm text-gray-600">
                <p>&copy; {{ date('Y') }} BookMania. Все права защищены.</p>
            </div>
        </div>
    </footer>
</body>
</html>