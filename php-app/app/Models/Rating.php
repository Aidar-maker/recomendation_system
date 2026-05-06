<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Rating extends Model
{
    protected $table = 'Ratings';
    protected $primaryKey = ['user_id', 'book_id'];
    public $incrementing = false;
    public $timestamps = false;

    protected $fillable = [
        'user_id',
        'book_id',
        'rating',
        'rated_at'
    ];

    public function user()
    {
        return $this->belongsTo(User::class, 'user_id', 'user_id');
    }

    public function book()
    {
        return $this->belongsTo(Book::class, 'book_id', 'book_id');
    }
}