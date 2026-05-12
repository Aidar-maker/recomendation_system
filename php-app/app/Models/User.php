<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Database\Factories\UserFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    /** @use HasFactory<UserFactory> */
    use HasFactory, Notifiable;


    protected $table = 'Users';
    protected $primaryKey = 'user_id';
    public $incrementing = true;  // ← true, т.к. auto_increment
    public $timestamps = false;   // ← false, т.к. у тебя created_at

    /**
     * The attributes that are mass assignable.
     *
     * @var list<string>
     */
    protected $fillable = [
        'login',
        'password_hash',  // ← ВАЖНО: password_hash
        'age',
        'location',
        'created_at'
    ];

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var list<string>
     */
    protected $hidden = [
        'password_hash',  // ← password_hash
    ];

    // Laravel использует 'password', а у нас 'password_hash'
    public function getAuthPassword()
    {
        return $this->password_hash;
    }

    public function getPasswordAttribute()
    {
        return $this->password_hash;
    }

    // Для логина по полю 'login'
    public function username()
    {
        return 'login';
    }

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'password_hash' => 'hashed',
            'created_at' => 'datetime',
        ];
    }

    public function ratings()
    {
        return $this->hasMany(Rating::class, 'user_id', 'user_id');
    }
}
