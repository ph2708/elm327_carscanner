<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class DiagnosticSession extends Model
{
    use HasUuids;

    protected $fillable = [
        'vehicle_id', 'status', 'port', 'protocol', 'adapter_version', 'supported_pids',
        'readiness_monitors', 'mil_active', 'dtc_count', 'started_at', 'ended_at'
    ];

    protected $casts = [
        'supported_pids' => 'array',
        'readiness_monitors' => 'array',
        'mil_active' => 'boolean',
        'dtc_count' => 'integer',
        'started_at' => 'datetime',
        'ended_at' => 'datetime',
    ];

    public function vehicle()
    {
        return $this->belongsTo(Vehicle::class);
    }

    public function frames()
    {
        return $this->hasMany(TelemetryFrame::class, 'session_id');
    }

    public function dtcs()
    {
        return $this->hasMany(SessionDtc::class, 'session_id');
    }

    public function findings()
    {
        return $this->hasMany(DiagnosticFinding::class, 'session_id');
    }
}
