<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class TelemetryFrame extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'session_id', 'captured_at', 'rpm', 'speed', 'coolant_temp', 'intake_temp',
        'map_kpa', 'maf_gs', 'tps', 'o2_b1s1', 'stft_b1', 'ltft_b1', 'extra_pids'
    ];

    protected $casts = [
        'captured_at' => 'datetime',
        'extra_pids' => 'array',
        'rpm' => 'float',
        'speed' => 'float',
        'coolant_temp' => 'float',
        'map_kpa' => 'float',
        'tps' => 'float',
        'o2_b1s1' => 'float',
        'stft_b1' => 'float',
        'ltft_b1' => 'float',
    ];

    public function session()
    {
        return $this->belongsTo(DiagnosticSession::class, 'session_id');
    }
}

