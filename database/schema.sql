CREATE DATABASE IF NOT EXISTS book_recommender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE book_recommender;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(60) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    location VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Book (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(60) NULL,
    title VARCHAR(260) NOT NULL,
    author VARCHAR(260) NOT NULL,
    year_publication INT NULL,
    publisher VARCHAR(60) NULL,
    image_url VARCHAR(250) NOT NULL DEFAULT '/images/no-cover.jpg'
);

CREATE TABLE Genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE Book_Genres (
    genre_id INT NOT NULL,
    book_id INT NOT NULL,
    PRIMARY KEY (genre_id, book_id),
    FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE
);

CREATE TABLE Ratings (
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    rating INT NULL CHECK (rating >= 1 AND rating <= 5),
    rated_at DATETIME NULL,
    PRIMARY KEY (user_id, book_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES Book(book_id) ON DELETE CASCADE
);

CREATE TABLE User_Preferences (
    user_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (user_id, genre_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE
);