<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\DiagnosticSession;
use App\Models\TelemetryFrame;
use App\Models\SessionDtc;
use App\Models\Vehicle;
use App\Services\RuleEngineService;
use Illuminate\Http\Request;

class TelemetryController extends Controller
{
    protected $ruleEngine;

    public function __construct(RuleEngineService $ruleEngine)
    {
        $this->ruleEngine = $ruleEngine;
    }

    /**
     * Inicia uma nova sessão de telemetria
     */
    public function startSession(Request $request)
    {
        $data = $request->validate([
            'vehicle_id' => 'nullable|uuid|exists:vehicles,id',
            'port' => 'nullable|string',
            'protocol' => 'nullable|string',
            'adapter_version' => 'nullable|string',
            'supported_pids' => 'nullable|array',
            'readiness_monitors' => 'nullable|array',
            'mil_active' => 'nullable|boolean',
            'dtc_count' => 'nullable|integer',
        ]);

        // Se não houver veículo informado, associa ao Ford Fiesta padrão
        if (empty($data['vehicle_id'])) {
            $defaultVehicle = Vehicle::firstOrCreate(
                ['vin' => '9BFB15FIESTA2014'],
                [
                    'make' => 'Ford',
                    'model' => 'New Fiesta',
                    'year' => 2014,
                    'engine' => '1.5 16V Sigma Flex',
                    'fuel_type' => 'Flex',
                    'metadata' => [
                        'idle_rpm' => 820,
                        'nominal_map_kpa' => [28, 36],
                        'normal_operating_temp' => [88, 102],
                    ]
                ]
            );
            $data['vehicle_id'] = $defaultVehicle->id;
        }

        $session = DiagnosticSession::create([
            'vehicle_id' => $data['vehicle_id'],
            'port' => $data['port'] ?? 'Simulador Virtual',
            'protocol' => $data['protocol'] ?? 'ISO 15765-4 (CAN 11/500)',
            'adapter_version' => $data['adapter_version'] ?? 'ELM327 v1.5',
            'supported_pids' => $data['supported_pids'] ?? [],
            'readiness_monitors' => $data['readiness_monitors'] ?? null,
            'mil_active' => $data['mil_active'] ?? false,
            'dtc_count' => $data['dtc_count'] ?? 0,
            'status' => 'ACTIVE',
            'started_at' => now(),
        ]);

        return response()->json([
            'status' => 'success',
            'session_id' => $session->id,
            'message' => 'Sessão de diagnóstico iniciada'
        ], 201);
    }

    /**
     * Recebe frames de telemetria em tempo real
     */
    public function storeFrames(Request $request)
    {
        $data = $request->validate([
            'session_id' => 'required|uuid|exists:diagnostic_sessions,id',
            'frames' => 'required|array|min:1',
            'frames.*.rpm' => 'nullable|numeric',
            'frames.*.speed' => 'nullable|numeric',
            'frames.*.coolant_temp' => 'nullable|numeric',
            'frames.*.intake_temp' => 'nullable|numeric',
            'frames.*.map_kpa' => 'nullable|numeric',
            'frames.*.tps' => 'nullable|numeric',
            'frames.*.o2_b1s1' => 'nullable|numeric',
            'frames.*.stft_b1' => 'nullable|numeric',
            'frames.*.ltft_b1' => 'nullable|numeric',
        ]);

        $sessionId = $data['session_id'];
        $insertedCount = 0;

        foreach ($data['frames'] as $frame) {
            TelemetryFrame::create([
                'session_id' => $sessionId,
                'rpm' => $frame['rpm'] ?? null,
                'speed' => $frame['speed'] ?? null,
                'coolant_temp' => $frame['coolant_temp'] ?? null,
                'intake_temp' => $frame['intake_temp'] ?? null,
                'map_kpa' => $frame['map_kpa'] ?? null,
                'tps' => $frame['tps'] ?? null,
                'o2_b1s1' => $frame['o2_b1s1'] ?? null,
                'stft_b1' => $frame['stft_b1'] ?? null,
                'ltft_b1' => $frame['ltft_b1'] ?? null,
                'captured_at' => now(),
            ]);
            $insertedCount++;
        }

        // Executa avaliação de regras a cada lote
        $session = DiagnosticSession::find($sessionId);
        $findings = $this->ruleEngine->evaluate($session);

        return response()->json([
            'status' => 'success',
            'inserted_frames' => $insertedCount,
            'active_findings' => count($findings)
        ]);
    }

    /**
     * Registra códigos DTC e Freeze Frame
     */
    public function storeDtcs(Request $request)
    {
        $data = $request->validate([
            'session_id' => 'required|uuid|exists:diagnostic_sessions,id',
            'dtcs' => 'required|array',
            'dtcs.*.code' => 'required|string',
            'dtcs.*.type' => 'nullable|string',
            'dtcs.*.description' => 'nullable|string',
            'dtcs.*.freeze_frame' => 'nullable|array',
            'readiness_monitors' => 'nullable|array',
            'mil_active' => 'nullable|boolean',
        ]);

        $session = DiagnosticSession::find($data['session_id']);
        if ($session) {
            if (isset($data['readiness_monitors'])) {
                $session->readiness_monitors = $data['readiness_monitors'];
            }
            if (isset($data['mil_active'])) {
                $session->mil_active = $data['mil_active'];
            }
            $session->dtc_count = count($data['dtcs']);
            $session->save();
        }

        $created = [];
        foreach ($data['dtcs'] as $dtc) {
            $created[] = SessionDtc::create([
                'session_id' => $data['session_id'],
                'code' => strtoupper($dtc['code']),
                'type' => $dtc['type'] ?? 'STORED',
                'description' => $dtc['description'] ?? null,
                'freeze_frame' => $dtc['freeze_frame'] ?? null,
            ]);
        }

        return response()->json([
            'status' => 'success',
            'recorded_dtcs' => count($created)
        ]);
    }
}
