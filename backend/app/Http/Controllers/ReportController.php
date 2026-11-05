<?php

namespace App\Http\Controllers;

use App\Models\DiagnosticSession;
use Illuminate\Http\Request;

class ReportController extends Controller
{
    public function show(string $id)
    {
        $session = DiagnosticSession::with(['vehicle', 'dtcs', 'findings'])->findOrFail($id);
        $frames = $session->frames()->latest('captured_at')->take(40)->get();

        $stats = [
            'avg_rpm' => $frames->avg('rpm'),
            'max_rpm' => $frames->max('rpm'),
            'avg_map' => $frames->avg('map_kpa'),
            'avg_coolant' => $frames->avg('coolant_temp'),
            'max_coolant' => $frames->max('coolant_temp'),
            'avg_stft' => $frames->avg('stft_b1'),
            'avg_ltft' => $frames->avg('ltft_b1'),
            'total_frames' => $session->frames()->count(),
        ];

        return view('reports.diagnostic_sheet', [
            'session' => $session,
            'stats' => $stats,
            'dtcs' => $session->dtcs,
            'findings' => $session->findings,
            'frames' => $frames,
        ]);
    }
}
