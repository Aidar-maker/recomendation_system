from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, DECIMAL, ForeignKey,
    UniqueConstraint, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    role = Column(String(20), nullable=False, server_default="user")
    created_at = Column(TIMESTAMP, server_default=func.now())

    favorites = relationship("Favorite", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    reading_statuses = relationship("ReadingStatus", back_populates="user")
    reading_progress = relationship("ReadingProgress", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    book_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    isbn = Column(String(13), unique=True, nullable=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    year_publication = Column(Integer, nullable=True)
    publisher = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    genres = relationship("BookGenre", back_populates="book")
    chapters = relationship("Chapter", back_populates="book")

class Genre(Base):
    __tablename__ = "genres"
    genre_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    genre_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class BookGenre(Base):
    __tablename__ = 'book_genre'

    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), primary_key=True)
    genre_id = Column(Integer, ForeignKey('genres.genre_id', ondelete='CASCADE'), primary_key=True)

    book = relationship("Book", back_populates="genres")
    genre = relationship("Genre", back_populates="books")

class Favorite(Base):
    __tablename__ = 'favorites'

    favorite_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    added_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='_user_fav_book_uc'),
    )

    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")

class ReadingStatus(Base):
    __tablename__ = 'reading_statuses'

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    
    status = Column(Integer, nullable=False) 
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='_user_status_book_uc'),
    )

    user = relationship("User", back_populates="reading_statuses")
    book = relationship("Book", back_populates="reading_statuses")

class Rating(Base):
    __tablename__ = 'ratings'

    rating_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)
    rated_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='_user_rating_book_uc'),
    )

    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")

# --- НОВЫЕ ТАБЛИЦЫ ДЛЯ MVP ---

class Chapter(Base):
    __tablename__ = "chapters"
    
    chapter_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content_html = Column(Text, nullable=False)
    order_number = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    book = relationship("Book", back_populates="chapters")

class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    
    progress_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.chapter_id", ondelete="SET NULL"), nullable=True)
    position_percent = Column(DECIMAL(5, 2), server_default="0", nullable=True)
    last_read_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book")
    chapter = relationship("Chapter")

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_progress'),
    )