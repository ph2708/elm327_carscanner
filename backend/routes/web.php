<?php

use Illuminate\Support\Facades\Route;
use App\Livewire\Dashboard;
use App\Livewire\Settings;
use App\Livewire\Sessions;
use App\Http\Controllers\ReportController;

Route::get('/', Dashboard::class);
Route::get('/sessions', Sessions::class);
Route::get('/settings', Settings::class);
Route::get('/report/{id}', [ReportController::class, 'show']);
