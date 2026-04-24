# Книжный Советник — Система Рекомендаций Книг
Персонализированная система рекомендаций книг на основе машинного обучения с интеграцией в библиотечные системы.
# Описание
Проект представляет собой микросервис рекомендательной системы, который может быть интегрирован в существующие библиотечные платформы. Система анализирует оценки пользователей и предлагает персонализированные рекомендации книг с использованием алгоритма NMF (Non-negative Matrix Factorization).
# Архитектура
Система состоит из следующих компонентов:
ML-SERVICE (FastAPI + Python) — сервис рекомендаций на порту 8000
MySQL БАЗА ДАННЫХ — хранение данных на порту 3306
PHP App — веб-приложение на порту 8080
phpMyAdmin — админка БД на порту 8081
Redis — кэширование на порту 6379
# Быстрый старт
Требования
Docker и Docker Compose
Python 3.9+ (для импорта данных)
MySQL клиент (опционально)
1. Клонирование проекта
Перейдите в папку проекта:
cd recomendation_system
2. Подготовка данных
Скачайте датасет Kaggle Books Dataset и разместите в папке data/:
data/
├── books.csv
├── users.csv
└── ratings.csv
3. Установка зависимостей Python
pip install pandas pymysql python-dotenv cryptography
4. Импорт данных
python import_kaggle_books.py
Время импорта: ~5-10 минут (зависит от размера датасета)
5. Запуск системы
docker-compose up -d --build
6. Проверка работы
ML API: http://localhost:8000
Swagger Docs: http://localhost:8000/docs
phpMyAdmin: http://localhost:8081
PHP App: http://localhost:8080
# API Документация
Базовый URL
http://localhost:8000
Аутентификация
Все запросы требуют API ключ в заголовке:
Authorization: Bearer secret-ml-api-key-2024
GET /health
Проверка работоспособности сервиса.
Ответ: {"status": "ok", "service": "ml-recommender"}
POST /api/v1/recommend
Получение персональных рекомендаций для пользователя.
Параметры:
user_id (int, обязательный) — ID пользователя
limit (int, необязательный) — Количество рекомендаций (по умолчанию 5)
Пример запроса: user_id=12345, limit=5
Ответ: массив книг с полями book_id, title, author, predicted_rating
POST /api/v1/similar
Получение похожих книг (контентная фильтрация по жанрам).
Параметры:
book_id (int, обязательный) — ID книги для поиска похожих
limit (int, необязательный) — Количество результатов (по умолчанию 5)
# Структура Базы Данных
Таблицы
Users — Пользователи системы (~278,858 записей)
Book — Каталог книг (~10,000+ записей)
Genres — Жанры книг (14 записей)
Book_Genres — Связь книг с жанрами (~15,000 записей)
Ratings — Оценки пользователей 1-10 (~1,000,000+ записей)
User_Preferences — Предпочтения пользователей
Поля таблиц
Users: user_id, login, password_hash, age, location, created_at
Book: book_id, isbn, title, author, year_publication, publisher, image_url
Genres: genre_id, genre_name
Book_Genres: genre_id, book_id (составной первичный ключ)
Ratings: user_id, book_id, rating, rated_at (составной первичный ключ)
User_Preferences: user_id, genre_id (составной первичный ключ)
# ML Алгоритм
NMF (Non-negative Matrix Factorization)
Система использует матричную факторизацию для выявления скрытых паттернов в оценках пользователей.
Принцип работы: создаётся матрица оценок (пользователи × книги), которая разлагается на скрытые факторы. На основе этих факторов предсказываются оценки для непрочитанных книг.
Параметры модели:
n_components: 20 (количество скрытых признаков)
random_state: 42 (воспроизводимость)
init: random (инициализация)
# Интеграция в Вашу Систему
PHP Пример
Создайте класс RecommendationClient с методом getRecommendations($userId, $limit). Используйте cURL для POST-запроса на /api/v1/recommend с заголовками Content-Type: application/json и Authorization: Bearer secret-ml-api-key-2024.
Python Пример
Используйте библиотеку requests для POST-запроса на endpoint /api/v1/recommend с JSON телом {"user_id": user_id, "limit": limit} и заголовками авторизации.
# Статистика Датасета
Пользователей: 278,858
Книг: ~270,000+
Оценок: ~1,000,000+
Диапазон оценок: 1-10
Средняя оценка: ~7.5
Жанров: 14
# Конфигурация
Переменные окружения
DB_HOST: 127.0.0.1 (хост базы данных)
DB_PORT: 3306 (порт MySQL)
DB_USER: bookuser (пользователь БД)
DB_PASS: bookpassword (пароль БД)
DB_NAME: book_recommender (имя базы данных)
API_KEY: secret-ml-api-key-2024 (ключ API)
ML_SERVICE_URL: http://ml-service:8000 (URL ML сервиса)
# Порты
MySQL: 3306
ML API: 8000
PHP App: 8080
phpMyAdmin: 8081
Redis: 6379
# Команды для Разработчиков
Просмотр логов: docker-compose logs -f ml-service
Перезапуск сервисов: docker-compose restart ml-service
Остановка всех сервисов: docker-compose down
Полная очистка: docker-compose down -v
Вход в контейнер: docker-compose exec db bash
Проверка статуса: docker-compose ps


# Пересборка системы рекомендаций
# Останавливаем
docker-compose down

# Собираем
docker-compose build ml-service

# Запускаем
docker-compose up -d ml-service

# Ждём 20 секунд
Start-Sleep -Seconds 20

# Смотрим логи
docker-compose logs ml-service --tail=50


# Откроет в браузере по умолчанию
Start-Process ".\demo.html"