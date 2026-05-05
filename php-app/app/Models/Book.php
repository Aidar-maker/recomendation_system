<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Book extends Model
{
    protected $table = 'Book';
    protected $primaryKey = 'book_id';
    public $incrementing = false;
    public $timestamps = false;

    protected $fillable = [
        'book_id',
        'isbn',
        'title',
        'author',
        'year_publication',
        'publisher',
        'image_url'
    ];

    public function ratings()
    {
        return $this->hasMany(Rating::class, 'book_id', 'book_id');
    }

    public function genres()
    {
        return $this->belongsToMany(Genre::class, 'Book_Genres', 'book_id', 'genre_id');
    }
}
