<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class UserBookStatus extends Model
{
    protected $table = 'user_book_status';
    
    protected $primaryKey = 'id';
    
    protected $fillable = [
        'user_id', 'book_id', 'status', 'rating', 'review', 
        'started_at', 'completed_at'
    ];
    
    protected $casts = [
        'started_at' => 'datetime',
        'completed_at' => 'datetime',
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