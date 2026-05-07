<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Validation\ValidationException;

class LoginController extends Controller
{
    // Показать форму входа
    public function showLoginForm()
    {
        return view('auth.login');
    }

    // Обработка входа
    public function login(Request $request)
    {
        // Валидация
        $request->validate([
            'login' => 'required|string',
            'password' => 'required|string',
        ]);

        // Попытка входа
        // Внимание: мы используем поле 'login' вместо 'email'
        if (Auth::attempt(['login' => $request->login, 'password' => $request->password])) {
            $request->session()->regenerate();
            
            // Если успешно - редирект на главную
            return redirect()->intended(route('home'));
        }

        // Если ошибка
        throw ValidationException::withMessages([
            'login' => 'Неверный логин или пароль.',
        ]);
    }

    // Выход
    public function logout(Request $request)
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();
        
        return redirect('/');
    }
}