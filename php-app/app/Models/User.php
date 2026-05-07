<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use HasFactory, Notifiable;

    protected $table = 'Users';
    protected $primaryKey = 'user_id';
    public $incrementing = false;
    public $timestamps = false;

    protected $fillable = [
        'user_id',
        'login',
        'password',
        'age',
        'location',
        'created_at'
    ];

    protected $hidden = [
        'password',
    ];

    public function username()
    {
        return 'login';
    }

    protected function casts(): array
    {
        return [
            'password' => 'hashed',
        ];
    }

    // Переопределяем имя поля для аутентификации
    public function getAuthIdentifierName()
    {
        return 'user_id';
    }

    // Переопределяем имя поля для имени пользователя
    public function getAuthIdentifier()
    {
        return $this->attributes[$this->primaryKey];
    }

    // Переопределяем имя поля для email (если нужно)
    public function getEmailForPasswordReset()
    {
        return $this->login;
    }

    // Связи
    public function ratings()
    {
        return $this->hasMany(Rating::class, 'user_id', 'user_id');
    }
}