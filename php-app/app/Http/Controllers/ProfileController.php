<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class ProfileController extends Controller
{
    public function edit()
    {
        return view('profile.edit', [
            'user' => Auth::user()
        ]);
    }

    public function update(Request $request)
    {
        $user = Auth::user();
        
        $validated = $request->validate([
            'age' => ['nullable', 'integer', 'min:0'],
            'location' => ['nullable', 'string', 'max:100'],
        ]);
        
        $user->age = $validated['age'] ?? $user->age;
        $user->location = $validated['location'] ?? $user->location;
        $user->save();
        
        return redirect()->back()->with('success', 'Профиль обновлён!');
    }

    public function destroy(Request $request)
    {
        $request->validate([
            'password' => ['required', 'current_password'],
        ]);
        
        $user = Auth::user();
        Auth::logout();
        $user->delete();
        
        $request->session()->invalidate();
        $request->session()->regenerateToken();
        
        return redirect('/');
    }
}