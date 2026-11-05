<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\TelemetryController;

Route::prefix('v1/telemetry')->group(function () {
    Route::post('/session/start', [TelemetryController::class, 'startSession']);
    Route::post('/frames', [TelemetryController::class, 'storeFrames']);
    Route::post('/dtcs', [TelemetryController::class, 'storeDtcs']);
});
