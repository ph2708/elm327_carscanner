<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\DiagnosticSession;
use App\Models\DiagnosticFinding;
use App\Models\SessionDtc;
use App\Models\TelemetryFrame;
use App\Services\GeminiDiagnosticService;

class Dashboard extends Component
{
    public ?string $sessionId = null;
    public ?string $aiAnalysis = null;
    public bool $isAnalyzing = false;
    public ?string $aiError = null;

    public function mount()
    {
        $session = DiagnosticSession::latest('started_at')->first();
        if ($session) {
            $this->sessionId = $session->id;
        }
    }

    public function analyzeWithGemini(GeminiDiagnosticService $service)
    {
        if (!$this->sessionId) {
            $this->aiError = 'Nenhuma sessão de diagnóstico ativa no momento.';
            return;
        }

        $session = DiagnosticSession::find($this->sessionId);
        if (!$session) {
            $this->aiError = 'Sessão não encontrada.';
            return;
        }

        $this->isAnalyzing = true;
        $this->aiError = null;
        $this->aiAnalysis = null;

        $result = $service->analyzeSession($session);

        $this->isAnalyzing = false;
        if ($result['success']) {
            $this->aiAnalysis = $result['analysis'];
        } else {
            $this->aiError = $result['message'];
        }
    }

    public function render()
    {
        $session = $this->sessionId ? DiagnosticSession::find($this->sessionId) : null;
        $latestFrame = $session ? $session->frames()->latest('captured_at')->first() : null;
        $dtcs = $session ? $session->dtcs()->latest()->get() : collect();
        $findings = $session ? $session->findings()->latest()->get() : collect();

        // Obtém os últimos 30 pontos para alimentar os gráficos do ApexCharts
        $chartData = [
            'labels' => [],
            'rpm' => [],
            'map' => [],
            'o2' => [],
            'stft' => [],
            'ltft' => [],
        ];

        if ($session) {
            $recentFrames = $session->frames()->latest('captured_at')->take(30)->get()->reverse();
            foreach ($recentFrames as $f) {
                $chartData['labels'][] = $f->captured_at ? $f->captured_at->format('H:i:s') : '';
                $chartData['rpm'][] = round($f->rpm ?? 0);
                $chartData['map'][] = round($f->map_kpa ?? 0, 1);
                $chartData['o2'][] = round($f->o2_b1s1 ?? 0, 2);
                $chartData['stft'][] = round($f->stft_b1 ?? 0, 1);
                $chartData['ltft'][] = round($f->ltft_b1 ?? 0, 1);
            }
        }

        return view('livewire.dashboard', [
            'session' => $session,
            'latest' => $latestFrame,
            'dtcs' => $dtcs,
            'findings' => $findings,
            'chartData' => $chartData,
        ]);
    }
}
