from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    favorites = relationship("Favorite", back_populates="user")
    reading_statuses = relationship("ReadingStatus", back_populates="user")
    ratings = relationship("Rating", back_populates="user")

class Book(Base):
    __tablename__ = 'books'

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String(13), unique=True, nullable=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    year_publication = Column(Integer, nullable=True)
    publisher = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    genres = relationship("BookGenre", back_populates="book")
    favorites = relationship("Favorite", back_populates="book")
    reading_statuses = relationship("ReadingStatus", back_populates="book")
    ratings = relationship("Rating", back_populates="book")

class Genre(Base):
    __tablename__ = 'genres'

    genre_id = Column(Integer, primary_key=True, autoincrement=True)
    genre_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    books = relationship("BookGenre", back_populates="genre")

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
    
    # 1=В планах, 2=Читаю, 3=Прочитано, 4=Брошено
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
    rating = Column(Integer, nullable=False) # 1-10
    rated_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='_user_rating_book_uc'),
    )

    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")