<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\DiagnosticSession;

class Sessions extends Component
{
    public function deleteSession(string $id)
    {
        $session = DiagnosticSession::find($id);
        if ($session) {
            $session->delete();
        }
    }

    public function render()
    {
        $sessions = DiagnosticSession::with(['vehicle'])
            ->withCount(['frames', 'dtcs', 'findings'])
            ->latest('started_at')
            ->paginate(15);

        return view('livewire.sessions', [
            'sessions' => $sessions
        ]);
    }
}
