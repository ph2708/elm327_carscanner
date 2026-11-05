<?php

namespace App\Services;

use App\Models\DiagnosticSession;
use App\Models\SystemSetting;
use Illuminate\Support\Facades\Http;
use Exception;

class GeminiDiagnosticService
{
    /**
     * Valida se a chave de API fornecida é válida
     */
    public function testConnection(string $apiKey): array
    {
        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
            ])->post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={$apiKey}", [
                'contents' => [
                    [
                        'parts' => [
                            ['text' => 'Responda apenas: OK']
                        ]
                    ]
                ]
            ]);

            if ($response->successful()) {
                return ['success' => true, 'message' => 'Conexão com Google Gemini realizada com sucesso!'];
            }

            $errorMsg = $response->json('error.message') ?? 'Chave de API inválida ou sem permissão.';
            return ['success' => false, 'message' => "Erro da API: {$errorMsg}"];
        } catch (Exception $e) {
            return ['success' => false, 'message' => "Falha na requisição: {$e->getMessage()}"];
        }
    }

    /**
     * Gera análise contextualizada dos dados do veículo
     */
    public function analyzeSession(DiagnosticSession $session): array
    {
        $apiKey = SystemSetting::get('gemini_api_key');
        if (!$apiKey) {
            return [
                'success' => false,
                'message' => 'Nenhuma chave de API do Gemini configurada. Acesse Configurações para adicionar sua chave gratuita.'
            ];
        }

        $vehicle = $session->vehicle;
        $dtcs = $session->dtcs()->get()->pluck('code')->toArray();
        $latestFrame = $session->frames()->latest('captured_at')->first();

        $prompt = "Você é um engenheiro automotivo especialista em injeção eletrônica e diagnóstico avançado com ferramentas de bancada (osciloscópio, manômetro, multímetro e termografia).\n";
        $prompt .= "Analise os seguintes dados coletados via scanner OBD-II:\n";
        $prompt .= "- Veículo: " . ($vehicle ? "{$vehicle->make} {$vehicle->model} {$vehicle->year} {$vehicle->engine} ({$vehicle->fuel_type})" : "Ford New Fiesta 1.5 16V Sigma Flex") . "\n";
        $prompt .= "- Códigos de Falha (DTCs): " . (!empty($dtcs) ? implode(', ', $dtcs) : "Nenhum DTC registrado no momento") . "\n";
        
        if ($latestFrame) {
            $prompt .= "- Telemetria Atual:\n";
            $prompt .= "  * RPM: {$latestFrame->rpm} rpm\n";
            $prompt .= "  * MAP: {$latestFrame->map_kpa} kPa (Faixa nominal Sigma: 28-36 kPa em marcha lenta quente)\n";
            $prompt .= "  * Temperatura da água (ECT): {$latestFrame->coolant_temp} °C\n";
            $prompt .= "  * Ajuste de Combustível Curto Prazo (STFT): {$latestFrame->stft_b1} %\n";
            $prompt .= "  * Ajuste de Combustível Longo Prazo (LTFT): {$latestFrame->ltft_b1} %\n";
            $prompt .= "  * Sonda Lambda B1S1: {$latestFrame->o2_b1s1} V\n";
            $prompt .= "  * Borboleta (TPS): {$latestFrame->tps} %\n";
        }

        $prompt .= "\nPor favor, forneça um laudo técnico estruturado em Markdown contendo:\n";
        $prompt .= "1. **Sintoma & Diagnóstico Preliminar**\n";
        $prompt .= "2. **Evidências Físicas nos Dados Coletados**\n";
        $prompt .= "3. **Causas Mais Prováveis**\n";
        $prompt .= "4. **Testes Práticos Recomendados (com parâmetros nominais esperados para NÃO trocar peças sem testar)**\n";

        try {
            $response = Http::withHeaders([
                'Content-Type' => 'application/json',
            ])->timeout(30)->post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={$apiKey}", [
                'contents' => [
                    [
                        'parts' => [
                            ['text' => $prompt]
                        ]
                    ]
                ]
            ]);

            if ($response->successful()) {
                $text = $response->json('candidates.0.content.parts.0.text');
                return [
                    'success' => true,
                    'analysis' => $text
                ];
            }

            return [
                'success' => false,
                'message' => 'Erro retornado pela API do Gemini: ' . ($response->json('error.message') ?? 'Desconhecido')
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Erro ao comunicar com o Gemini: ' . $e->getMessage()
            ];
        }
    }
}

