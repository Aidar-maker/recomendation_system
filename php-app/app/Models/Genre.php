<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Genre extends Model
{
    protected $table = 'Genres';
    protected $primaryKey = 'genre_id';
    public $timestamps = false;

    protected $fillable = ['genre_id', 'genre_name'];

    public function books()
    {
        return $this->belongsToMany(Book::class, 'Book_Genres', 'genre_id', 'book_id');
    }

    public function users()
    {
        return $this->belongsToMany(User::class, 'User_Preferences', 'genre_id', 'user_id');
    }
}
