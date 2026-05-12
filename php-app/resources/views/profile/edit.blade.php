@extends('layouts.app')

@section('title', 'Профиль')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Профиль</h1>
    
    <div class="bg-white rounded-lg shadow p-6">
        <dl class="space-y-4">
            <div>
                <dt class="font-semibold text-gray-700">Логин:</dt>
                <dd class="text-gray-600">{{ Auth::user()->login }}</dd>
            </div>
            
            <div>
                <dt class="font-semibold text-gray-700">Возраст:</dt>
                <dd class="text-gray-600">{{ Auth::user()->age ?? 'Не указан' }}</dd>
            </div>
            
            <div>
                <dt class="font-semibold text-gray-700">Город:</dt>
                <dd class="text-gray-600">{{ Auth::user()->location ?? 'Не указан' }}</dd>
            </div>
        </dl>
    </div>
</div>
@endsection