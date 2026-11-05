<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class DiagnosticFinding extends Model
{
    use HasUuids;

    protected $fillable = [
        'session_id', 'source', 'symptom', 'supporting_data', 'possible_causes',
        'confidence_percent', 'recommended_tests', 'expected_outcome'
    ];

    protected $casts = [
        'supporting_data' => 'array',
        'possible_causes' => 'array',
        'confidence_percent' => 'integer'
    ];

    public function session()
    {
        return $this->belongsTo(DiagnosticSession::class, 'session_id');
    }
}

