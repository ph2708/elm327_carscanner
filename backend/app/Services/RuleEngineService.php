<?php

namespace App\Services;

use App\Models\DiagnosticSession;
use App\Models\DiagnosticFinding;

class RuleEngineService
{
    /**
     * Avalia as regras especialistas sobre os dados da sessão
     */
    public function evaluate(DiagnosticSession $session): array
    {
        $findings = [];
        $frames = $session->frames()->latest('captured_at')->take(50)->get();

        if ($frames->isEmpty()) {
            return $findings;
        }

        // Calcula médias recentes
        $avgRpm = $frames->avg('rpm');
        $avgLtft = $frames->avg('ltft_b1');
        $avgStft = $frames->avg('stft_b1');
        $avgCoolant = $frames->avg('coolant_temp');
        $avgMap = $frames->avg('map_kpa');

        // Regra 1: Entrada falsa de ar na admissão (Mistura Pobre em Marcha Lenta)
        // No New Fiesta 1.5 (Motor Sigma), marcha lenta é ~800 RPM e MAP nominal é 28 a 36 kPa
        if ($avgRpm < 950 && $avgLtft > 12.0) {
            $findings[] = DiagnosticFinding::create([
                'session_id' => $session->id,
                'source' => 'RULE_ENGINE',
                'symptom' => 'Correção de combustível a longo prazo (LTFT) excessivamente positiva em marcha lenta',
                'supporting_data' => [
                    'avg_rpm' => round($avgRpm, 1),
                    'avg_ltft' => round($avgLtft, 2),
                    'avg_stft' => round($avgStft, 2),
                    'avg_map_kpa' => round($avgMap, 1),
                ],
                'possible_causes' => [
                    'Entrada falsa de ar (junta do coletor de admissão ressecada)',
                    'Mangueira de respiro do cárter (Blow-by/PCV) trincada',
                    'Bico injetor parcialmente obstruído',
                    'Baixa pressão da bomba de combustível'
                ],
                'confidence_percent' => 88,
                'recommended_tests' => "1. Realizar teste de estanqueidade com máquina de fumaça na admissão.\n2. Inspecionar mangueiras de vácuo do servo-freio e cânister.\n3. Medir pressão e vazão da linha de combustível.",
                'expected_outcome' => "Ausência total de vazamentos de fumaça; Pressão da linha em 3.8 a 4.2 bar constantes."
            ]);
        }

        // Regra 2: Válvula termostática aberta ou sensor ECT descalibrado
        if ($frames->count() >= 30 && $avgCoolant < 70.0 && $avgRpm > 1200) {
            $findings[] = DiagnosticFinding::create([
                'session_id' => $session->id,
                'source' => 'RULE_ENGINE',
                'symptom' => 'Motor operando abaixo da faixa térmica ideal mesmo em funcionamento contínuo',
                'supporting_data' => [
                    'avg_coolant_temp' => round($avgCoolant, 1),
                    'expected_min_temp' => 85.0
                ],
                'possible_causes' => [
                    'Válvula termostática travada aberta mecânica ou eletronicamente',
                    'Sensor de temperatura do líquido de arrefecimento (ECT) descalibrado'
                ],
                'confidence_percent' => 85,
                'recommended_tests' => "1. Medir temperatura real da carcaça do termostato com termômetro infravermelho.\n2. Comparar resistência do sensor ECT com a tabela de calibração.",
                'expected_outcome' => "Temperatura atingir entre 88°C e 96°C antes da liberação para o radiador."
            ]);
        }

        return $findings;
    }
}

