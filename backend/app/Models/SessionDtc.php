<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class SessionDtc extends Model
{
    use HasUuids;

    protected $table = 'session_dtcs';

    protected $fillable = [
        'session_id', 'code', 'type', 'description', 'freeze_frame'
    ];

    protected $casts = [
        'freeze_frame' => 'array'
    ];

    public function session()
    {
        return $this->belongsTo(DiagnosticSession::class, 'session_id');
    }
}
