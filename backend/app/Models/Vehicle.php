<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class Vehicle extends Model
{
    use HasUuids;

    protected $fillable = [
        'vin', 'make', 'model', 'year', 'engine', 'fuel_type', 'metadata'
    ];

    protected $casts = [
        'metadata' => 'array',
        'year' => 'integer'
    ];

    public function sessions()
    {
        return $this->hasMany(DiagnosticSession::class);
    }
}

