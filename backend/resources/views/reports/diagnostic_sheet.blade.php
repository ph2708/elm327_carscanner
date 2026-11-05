<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Laudo Técnico de Diagnóstico — AutoScan BR</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {
            .no-print { display: none !important; }
            body { background: white !important; color: black !important; }
            .print-border { border-color: #cbd5e1 !important; }
        }
    </style>
</head>
<body class="bg-slate-100 text-slate-800 font-sans p-6 md:p-12">
    <div class="max-w-4xl mx-auto bg-white p-8 md:p-12 rounded-2xl shadow-xl print:shadow-none print:p-0">
        <!-- Barra de Ações para Impressão -->
        <div class="no-print flex items-center justify-between pb-6 mb-6 border-b border-slate-200">
            <a href="/sessions" class="text-sm font-semibold text-indigo-600 hover:text-indigo-800">← Voltar para Histórico</a>
            <button onclick="window.print()" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-lg shadow-md transition flex items-center space-x-2">
                <span>🖨 Imprimir / Salvar em PDF</span>
            </button>
        </div>

        <!-- Cabeçalho do Laudo -->
        <div class="flex items-start justify-between border-b-2 border-slate-900 pb-6 mb-6">
            <div>
                <h1 class="text-2xl font-black tracking-tight text-slate-900">AUTOSCAN BR</h1>
                <p class="text-xs font-semibold uppercase tracking-widest text-indigo-600">Laudo Técnico de Diagnóstico e Telemetria OBD-II</p>
                <p class="text-xs text-slate-500 mt-1">ID da Sessão: {{ $session->id }}</p>
            </div>
            <div class="text-right">
                <span class="inline-block px-3 py-1 bg-slate-900 text-white text-xs font-mono font-bold rounded">
                    {{ $session->started_at ? $session->started_at->format('d/m/Y H:i') : now()->format('d/m/Y H:i') }}
                </span>
                <p class="text-xs text-slate-500 mt-1">Status: Concluído / Registrado</p>
            </div>
        </div>

        <!-- Dados do Veículo & Conexão -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6 text-xs">
            <div>
                <span class="text-slate-400 font-semibold block uppercase">Veículo</span>
                <strong class="text-slate-900 text-sm">{{ $session->vehicle ? $session->vehicle->make . ' ' . $session->vehicle->model : 'Ford New Fiesta' }}</strong>
            </div>
            <div>
                <span class="text-slate-400 font-semibold block uppercase">Motorização</span>
                <strong class="text-slate-900 text-sm">{{ $session->vehicle ? $session->vehicle->engine . ' ' . $session->vehicle->fuel_type : '1.5 16V Sigma Flex' }}</strong>
            </div>
            <div>
                <span class="text-slate-400 font-semibold block uppercase">Protocolo OBD-II</span>
                <strong class="text-slate-900 font-mono">{{ $session->protocol ?? 'ISO 15765-4 (CAN 11/500)' }}</strong>
            </div>
            <div>
                <span class="text-slate-400 font-semibold block uppercase">Adaptador</span>
                <strong class="text-slate-900 font-mono">{{ $session->adapter_version ?? 'ELM327 v1.5' }}</strong>
            </div>
        </div>

        <!-- Resumo Estatístico de Telemetria -->
        <div class="mb-8">
            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-900 mb-3 border-b pb-1">1. Médias de Funcionamento Durante o Ensaio</h2>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span class="text-[11px] text-slate-500 block">RPM Médio / Máx</span>
                    <strong class="text-base text-slate-900 font-mono">{{ round($stats['avg_rpm'] ?? 0) }} / {{ round($stats['max_rpm'] ?? 0) }}</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span class="text-[11px] text-slate-500 block">Pressão MAP Média</span>
                    <strong class="text-base text-slate-900 font-mono">{{ round($stats['avg_map'] ?? 0, 1) }} kPa</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span class="text-[11px] text-slate-500 block">Temp. Arrefecimento</span>
                    <strong class="text-base text-slate-900 font-mono">{{ round($stats['avg_coolant'] ?? 0, 1) }}°C</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span class="text-[11px] text-slate-500 block">Ajuste Longo Prazo (LTFT)</span>
                    <strong class="text-base font-mono {{ ($stats['avg_ltft'] ?? 0) > 10 ? 'text-rose-600' : 'text-slate-900' }}">
                        {{ ($stats['avg_ltft'] ?? 0) > 0 ? '+' : '' }}{{ round($stats['avg_ltft'] ?? 0, 1) }}%
                    </strong>
                </div>
            </div>
        </div>

        <!-- Códigos de Falha Armazenados (DTCs) -->
        <div class="mb-8">
            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-900 mb-3 border-b pb-1">2. Códigos de Diagnóstico de Falha (DTCs)</h2>
            @if ($dtcs->isEmpty())
                <div class="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs">
                    ✓ Nenhum código de falha ativo ou pendente registrado na ECU.
                </div>
            @else
                <div class="space-y-2">
                    @foreach ($dtcs as $dtc)
                        <div class="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center justify-between text-xs">
                            <div>
                                <span class="font-mono font-bold text-rose-700 text-sm">{{ $dtc->code }}</span>
                                <span class="ml-2 font-semibold uppercase text-slate-600">[{{ $dtc->type }}]</span>
                                <p class="text-slate-700 mt-0.5">
                                    {{ $dtc->code === 'P0171' ? 'Sistema muito pobre (Bancada 1) - Mistura de ar e combustível desbalanceada' : 'Falha reportada pela ECU' }}
                                </p>
                            </div>
                            <span class="text-[10px] text-slate-400 font-mono">{{ $dtc->created_at->format('H:i:s') }}</span>
                        </div>
                    @endforeach
                </div>
            @endif
        </div>

        <!-- Parecer do Motor de Regras Especialistas -->
        <div class="mb-8">
            <h2 class="text-sm font-bold uppercase tracking-wider text-slate-900 mb-3 border-b pb-1">3. Conclusão Diagnóstica & Testes Físicos de Validação</h2>
            @if ($findings->isEmpty())
                <p class="text-xs text-slate-500">Parâmetros analisados dentro dos limites nominais aceitáveis.</p>
            @else
                <div class="space-y-4">
                    @foreach ($findings as $finding)
                        <div class="p-4 bg-slate-50 border border-slate-300 rounded-xl text-xs space-y-2">
                            <div class="flex items-center justify-between">
                                <strong class="text-sm text-slate-900">{{ $finding->symptom }}</strong>
                                <span class="px-2 py-0.5 bg-amber-100 text-amber-800 font-bold rounded">
                                    Confiança da Hipótese: {{ $finding->confidence_percent }}%
                                </span>
                            </div>

                            <div>
                                <span class="font-semibold text-slate-600 block">Hipóteses e Causas Mecânicas/Eletrônicas:</span>
                                <ul class="list-disc list-inside text-slate-700 mt-1 space-y-0.5">
                                    @foreach ($finding->possible_causes as $cause)
                                        <li>{{ $cause }}</li>
                                    @endforeach
                                </ul>
                            </div>

                            <div class="p-3 bg-white border border-slate-200 rounded-lg">
                                <strong class="text-indigo-700 block mb-1">Procedimento Instrumentado Recomendado (Antes de Trocar Peças):</strong>
                                <p class="text-slate-800 whitespace-pre-wrap">{{ $finding->recommended_tests }}</p>
                                <p class="mt-2 text-emerald-700 font-semibold">Valor Nominal Esperado: {{ $finding->expected_outcome }}</p>
                            </div>
                        </div>
                    @endforeach
                </div>
            @endif
        </div>

        <!-- Assinatura Técnica -->
        <div class="pt-12 mt-12 border-t border-slate-300 grid grid-cols-2 gap-8 text-center text-xs text-slate-600">
            <div>
                <div class="border-b border-slate-400 pb-8 mb-2"></div>
                <p class="font-bold text-slate-800">Técnico / Responsável pelo Diagnóstico</p>
                <p class="text-[11px] text-slate-400">Oficina / Inspeção Veicular</p>
            </div>
            <div>
                <div class="border-b border-slate-400 pb-8 mb-2"></div>
                <p class="font-bold text-slate-800">Proprietário do Veículo</p>
                <p class="text-[11px] text-slate-400">Ciente do Laudo Preliminar</p>
            </div>
        </div>
    </div>
</body>
</html>

