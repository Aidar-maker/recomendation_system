<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use Illuminate\Validation\Rules;
use Illuminate\Validation\ValidationException;
use Illuminate\View\View;

class RegisteredUserController extends Controller
{
    public function create(): View
    {
        return view('auth.register');
    }

    public function store(Request $request): RedirectResponse
    {
        $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'lowercase', 'email', 'max:255', 'unique:Users,email'],
            'password' => ['required', 'confirmed', Rules\Password::defaults()],
        ]);

        // Генерируем login из email (убираем @ и домен)
        $login = Str::before($request->email, '@');
        
        // Проверяем уникальность login
        $originalLogin = $login;
        $counter = 1;
        while (User::where('login', $login)->exists()) {
            $login = $originalLogin . $counter;
            $counter++;
        }

        $user = User::create([
            'name' => $request->name,
            'email' => $request->email,
            'login' => $login,
            'password_hash' => Hash::make($request->password),
        ]);

        event(new Registered($user));

        Auth::login($user);

        return redirect(route('home', absolute: false));
    }
}