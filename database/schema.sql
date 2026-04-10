CREATE DATABASE IF NOT EXISTS book_recommender 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Переключаемся на созданную базу данных
USE book_recommender;

-- ТАБЛИЦА 1: Users (Пользователи)
-- Хранит учётные данные всех пользователей системы
-- Эти данные используются для:
-- - Авторизации в системе
-- - Персонализации рекомендаций (по user_id)
CREATE TABLE Users (
    -- Уникальный идентификатор пользователя
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Логин пользователя
    login VARCHAR(60) NOT NULL UNIQUE,
    
    -- Хэш пароля (НИКОГДА не храним пароли в открытом виде!)

    password_hash VARCHAR(255) NOT NULL,
    
    -- Возраст пользователя
    age INT NOT NULL,
    
    location VARCHAR(100) NULL,
    
    -- Дата и время регистрации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ТАБЛИЦА 2: Book (Книги)
-- Каталог всех книг в системе
-- Эти данные используются для:
-- - Отображения в каталоге
-- - Контентной фильтрации (по автору, жанру, году)
CREATE TABLE Book (
    -- Уникальный идентификатор книги
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- ISBN - международный стандартный номер книги
    isbn VARCHAR(60) NULL,
    
    -- Название книги
    title VARCHAR(260) NOT NULL,
    
    -- Автор книги
    author VARCHAR(260) NOT NULL,
    
    -- Год публикации
    year_publication INT NULL,
    
    -- Издательство
    publisher VARCHAR(60) NULL,
    
    -- URL
    -- DEFAULT
    image_url VARCHAR(250) NOT NULL DEFAULT '/images/no-cover.jpg'
);


-- ТАБЛИЦА 3: Genres (Жанры)
-- Справочник жанров (Фантастика, Детектив, Роман и т.д.)
-- Вынесено в отдельную таблицу для:
-- - Уменьшения дублирования данных
-- - Удобной фильтрации по жанрам
-- - Анализа предпочтений пользователей
CREATE TABLE Genres (
    -- Уникальный идентификатор жанра
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Название жанра
    -- VARCHAR(20) - достаточно коротких названий
    -- UNIQUE - нельзя создать два жанра с одинаковым названием
    genre_name VARCHAR(20) NOT NULL UNIQUE
);

-- ТАБЛИЦА 4: Book_Genres (Связь книг и жанров)
-- Таблица связи "многие-ко-многим"
-- Одна книга может иметь несколько жанров
-- Один жанр может быть у многих книг
CREATE TABLE Book_Genres (
    -- ID жанра (ссылка на таблицу Genres)
    genre_id INT NOT NULL,
    
    -- ID книги (ссылка на таблицу Book)
    book_id INT NOT NULL,
    
    -- Составной первичный ключ
    -- Одна и та же пара (genre_id, book_id) не может повториться
    PRIMARY KEY (genre_id, book_id),
    
    -- Внешние ключи (FOREIGN KEY) - обеспечивают целостность данных
    -- ON DELETE CASCADE - если удалим жанр, удалятся все связи с ним
    FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE
);

-- ТАБЛИЦА 5: Ratings (Оценки пользователей)
-- САМАЯ ВАЖНАЯ ТАБЛИЦА ДЛЯ ML-АЛГОРИТМОВ!
-- На основе этих данных строится матрица "пользователь × книга"
CREATE TABLE Ratings (
    -- ID пользователя (кто оценил)
    user_id INT NOT NULL,
    
    -- ID книги (что оценили)
    book_id INT NOT NULL,
    
    -- Оценка от 1 до 5 звезд
    -- INT - целое число
    -- CHECK - ограничение диапазона
    -- NULL - разрешён для случаев, когда книга добавлена в "хочу прочитать"
    rating INT NULL CHECK (rating >= 1 AND rating <= 5),
    
    -- Дата и время оценки
    -- DATETIME - точная дата для анализа временных паттернов
    rated_at DATETIME NULL,
