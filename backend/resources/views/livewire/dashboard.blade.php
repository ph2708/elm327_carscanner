<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6" wire:poll.1000ms>
    <!-- Header com status da conexão -->
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div class="flex items-center space-x-4">
            <div class="w-3.5 h-3.5 rounded-full {{ $session ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600' }}"></div>
            <div>
                <h1 class="text-xl font-bold text-white tracking-wide">AutoScan BR — Telemetria Veicular</h1>
                <p class="text-xs text-slate-400">
                    Veículo: <span class="text-indigo-400 font-semibold">{{ $session && $session->vehicle ? $session->vehicle->make . ' ' . $session->vehicle->model . ' ' . $session->vehicle->engine : 'Ford New Fiesta 1.5 16V Sigma Flex' }}</span> | 
                    Porta: <span class="text-slate-300 font-mono">{{ $session->port ?? 'Desconectado' }}</span> | 
                    Protocolo: <span class="text-slate-300">{{ $session->protocol ?? 'Aguardando Handshake' }}</span>
                </p>
            </div>
        </div>

        <div class="flex items-center space-x-3">
            @if ($session && $session->mil_active)
                <span class="px-3 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold rounded-lg flex items-center space-x-1 animate-pulse">
                    <span>⚡ LUZ DE INJEÇÃO (MIL) ACESA</span>
                </span>
            @endif

            <button wire:click="analyzeWithGemini" wire:loading.attr="disabled"
                    class="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-500/20 transition flex items-center space-x-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span wire:loading.remove wire:target="analyzeWithGemini">Análise com Gemini AI</span>
                <span wire:loading wire:target="analyzeWithGemini">Consultando IA...</span>
            </button>
            <a href="/settings" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition">
                ⚙ Configurar API
            </a>
        </div>
    </div>

    <!-- Feedback / Painel de Análise por IA -->
    @if ($aiError)
        <div class="bg-rose-950/40 border border-rose-500/40 p-4 rounded-xl text-rose-300 text-sm flex items-center justify-between">
            <span>⚠ {{ $aiError }}</span>
            <a href="/settings" class="underline text-xs font-semibold">Configurar Chave</a>
        </div>
    @endif

    @if ($aiAnalysis)
        <div class="bg-slate-900 border border-indigo-500/50 rounded-xl p-6 shadow-2xl relative overflow-hidden">
            <div class="absolute top-0 right-0 px-3 py-1 bg-indigo-600 text-[10px] uppercase font-black tracking-widest text-white rounded-bl-lg">
                Laudo Inteligente Gemini AI
            </div>
            <h3 class="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                <span>🤖 Diagnóstico de Engenharia & Mecânica</span>
            </h3>
            <div class="prose prose-invert prose-indigo max-w-none text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                {{ $aiAnalysis }}
            </div>
        </div>
    @endif

    <!-- Gauges e Mostradores Principais -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <!-- RPM -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">RPM Motor</span>
            <div class="text-3xl font-black text-white font-mono mt-1">
                {{ $latest ? number_format($latest->rpm, 0) : '0' }}
            </div>
            <span class="text-[11px] text-slate-500">rpm (Lenta: ~820)</span>
        </div>

        <!-- Velocidade -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Velocidade</span>
            <div class="text-3xl font-black text-emerald-400 font-mono mt-1">
                {{ $latest ? number_format($latest->speed, 0) : '0' }}
            </div>
            <span class="text-[11px] text-slate-500">km/h</span>
        </div>

        <!-- MAP (Pressão no Coletor) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sensor MAP</span>
            <div class="text-3xl font-black text-cyan-400 font-mono mt-1">
                {{ $latest ? number_format($latest->map_kpa, 1) : '--' }}
            </div>
            <span class="text-[11px] text-slate-500">kPa (Nominal: 28-36)</span>
        </div>

        <!-- Temperatura Arrefecimento -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Líquido Arrefec.</span>
            <div class="text-3xl font-black text-amber-400 font-mono mt-1">
                {{ $latest ? number_format($latest->coolant_temp, 1) : '--' }}°C
            </div>
            <span class="text-[11px] text-slate-500">Faixa: 88-102°C</span>
        </div>

        <!-- STFT (Curto Prazo) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ajuste STFT</span>
            <div class="text-3xl font-black {{ ($latest && abs($latest->stft_b1) > 10) ? 'text-rose-400' : 'text-slate-200' }} font-mono mt-1">
                {{ $latest ? ($latest->stft_b1 > 0 ? '+' : '') . number_format($latest->stft_b1, 1) : '--' }}%
            </div>
            <span class="text-[11px] text-slate-500">Alvo: -5% a +5%</span>
        </div>

        <!-- LTFT (Longo Prazo) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
            <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ajuste LTFT</span>
            <div class="text-3xl font-black {{ ($latest && abs($latest->ltft_b1) > 10) ? 'text-rose-400' : 'text-slate-200' }} font-mono mt-1">
                {{ $latest ? ($latest->ltft_b1 > 0 ? '+' : '') . number_format($latest->ltft_b1, 1) : '--' }}%
            </div>
            <span class="text-[11px] text-slate-500">Alvo: -10% a +10%</span>
        </div>
    </div>

    <!-- Gráficos de Osciloscópio em Tempo Real (ApexCharts) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" wire:ignore>
        <!-- Gráfico 1: Sonda Lambda B1S1 (Tensão de Resposta) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider">Sonda Lambda B1S1 (Tensão de Mistura)</h3>
                <span class="text-xs text-indigo-400 font-mono">0.1V (Pobre) ↔ 0.9V (Rica)</span>
            </div>
            <div id="chart-lambda" style="min-height: 220px;"></div>
        </div>

        <!-- Gráfico 2: Ajuste de Combustível (STFT vs LTFT) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider">Correção de Combustível (STFT vs LTFT)</h3>
                <span class="text-xs text-emerald-400 font-mono">Curto e Longo Prazo (%)</span>
            </div>
            <div id="chart-fuel" style="min-height: 220px;"></div>
        </div>
    </div>

    <!-- Monitores de Prontidão (Readiness Monitors - Modo 01 PID 01) -->
    @if ($session && $session->readiness_monitors)
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <span>🛡️ Monitores de Prontidão de Emissões (I/M Readiness)</span>
                </h3>
                <span class="text-xs text-slate-400 font-mono">Modo 01 PID 01</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 text-xs">
                @foreach ($session->readiness_monitors as $monitorName => $status)
                    <div class="p-2.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between">
                        <span class="text-slate-300 font-medium truncate mr-2">{{ $monitorName }}</span>
                        @if ($status === 'COMPLETO')
                            <span class="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 font-bold text-[10px] rounded">
                                PRONTO
                            </span>
                        @else
                            <span class="px-2 py-0.5 bg-amber-500/20 text-amber-400 font-bold text-[10px] rounded animate-pulse">
                                INCOMPLETO
                            </span>
                        @endif
                    </div>
                @endforeach
            </div>
        </div>
    @endif

    <!-- Sessão Inferior: DTCs com Freeze Frame e Diagnósticos Especialistas -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Códigos de Erro Detectados e Freeze Frame (Modos 02, 03 e 07) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 class="text-base font-bold text-white mb-4 flex items-center justify-between">
                <span>Códigos de Falha DTC & Freeze Frame</span>
                <span class="text-xs px-2 py-0.5 rounded-full {{ $dtcs->count() > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400' }}">
                    {{ $dtcs->count() }} Ativo(s)
                </span>
            </h2>

            @if ($dtcs->isEmpty())
                <div class="text-center py-8 text-slate-500 text-sm">
                    Nenhum código de falha detectado na ECU.
                </div>
            @else
                <div class="space-y-4">
                    @foreach ($dtcs as $dtc)
                        <div class="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="font-mono font-bold text-rose-400 text-lg">{{ $dtc->code }}</span>
                                    <span class="ml-2 text-xs text-slate-400 uppercase font-semibold">[{{ $dtc->type }}]</span>
                                </div>
                                <span class="text-[10px] text-slate-500">{{ $dtc->created_at->diffForHumans() }}</span>
                            </div>

                            <p class="text-xs text-slate-300">
                                {{ $dtc->description ?? ($dtc->code === 'P0171' ? 'Sistema muito pobre (Bancada 1) - Excesso de ar ou falta de combustível' : 'Código de falha OBD padrão') }}
                            </p>

                            <!-- Dados Congelados no Momento da Falha (Freeze Frame) -->
                            @if ($dtc->freeze_frame)
                                <div class="mt-2 p-2.5 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px]">
                                    <span class="font-bold text-cyan-400 uppercase tracking-wider block mb-1.5">
                                        📸 Freeze Frame (Condição no Momento do Erro):
                                    </span>
                                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 text-slate-400 font-mono">
                                        @foreach ($dtc->freeze_frame as $key => $val)
                                            <div>
                                                <span class="text-slate-500">{{ strtoupper(str_replace('_', ' ', $key)) }}:</span>
                                                <strong class="text-slate-200">{{ is_array($val) ? json_encode($val) : $val }}</strong>
                                            </div>
                                        @endforeach
                                    </div>
                                </div>
                            @endif
                        </div>
                    @endforeach
                </div>
            @endif
        </div>

        <!-- Laudos do Motor de Regras Local (Sem Trocação Cega de Peças) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
            <h2 class="text-base font-bold text-white mb-4 flex items-center justify-between">
                <span>Motor de Inferência Diagnóstica</span>
                <span class="text-xs text-indigo-400 font-semibold">Análise Determinística</span>
            </h2>

            @if ($findings->isEmpty())
                <div class="text-center py-8 text-slate-500 text-sm">
                    Aguardando frames suficientes para análise estatística de comportamento.
                </div>
            @else
                <div class="space-y-4">
                    @foreach ($findings as $finding)
                        <div class="p-4 bg-slate-950 border border-amber-500/30 rounded-xl">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-bold text-amber-300">{{ $finding->symptom }}</span>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">
                                    Confiança: {{ $finding->confidence_percent }}%
                                </span>
                            </div>

                            <div class="text-xs text-slate-400 mb-2">
                                <strong class="text-slate-300">Causas prováveis:</strong>
                                <ul class="list-disc list-inside mt-1 space-y-0.5">
                                    @foreach ($finding->possible_causes as $cause)
                                        <li>{{ $cause }}</li>
                                    @endforeach
                                </ul>
                            </div>

                            <div class="p-2.5 bg-slate-900 rounded-lg text-xs border border-slate-800 mt-2">
                                <strong class="text-indigo-400">Testes instrumentados recomendados:</strong>
                                <p class="text-slate-300 mt-1 whitespace-pre-wrap">{{ $finding->recommended_tests }}</p>
                                <p class="text-emerald-400 mt-1"><strong>Resultado esperado:</strong> {{ $finding->expected_outcome }}</p>
                            </div>
                        </div>
                    @endforeach
                </div>
            @endif
        </div>
    </div>

    <!-- Script de Inicialização e Atualização do ApexCharts -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const initialData = @json($chartData);

            // Gráfico de Sonda Lambda
            const lambdaOptions = {
                chart: {
                    type: 'area',
                    height: 220,
                    animations: { enabled: true, easing: 'linear', dynamicAnimation: { speed: 800 } },
                    toolbar: { show: false },
                    background: 'transparent'
                },
                theme: { mode: 'dark' },
                stroke: { curve: 'smooth', width: 2 },
                series: [{ name: 'Sonda O2 B1S1 (V)', data: initialData.o2 }],
                xaxis: { categories: initialData.labels, labels: { show: false } },
                yaxis: { min: 0.0, max: 1.0, decimalsInFloat: 2 },
                colors: ['#6366f1'],
                fill: {
                    type: 'gradient',
                    gradient: { shadeIntensity: 1, opacityFrom: 0.5, opacityTo: 0.05, stops: [0, 90, 100] }
                },
                grid: { borderColor: '#1e293b' }
            };
            const lambdaChart = new ApexCharts(document.querySelector("#chart-lambda"), lambdaOptions);
            lambdaChart.render();

            // Gráfico de Trim de Combustível (STFT vs LTFT)
            const fuelOptions = {
                chart: {
                    type: 'line',
                    height: 220,
                    animations: { enabled: true, easing: 'linear', dynamicAnimation: { speed: 800 } },
                    toolbar: { show: false },
                    background: 'transparent'
                },
                theme: { mode: 'dark' },
                stroke: { curve: 'smooth', width: 2 },
                series: [
                    { name: 'STFT (%)', data: initialData.stft },
                    { name: 'LTFT (%)', data: initialData.ltft }
                ],
                xaxis: { categories: initialData.labels, labels: { show: false } },
                yaxis: { min: -25, max: 25 },
                colors: ['#38bdf8', '#f43f5e'],
                grid: { borderColor: '#1e293b' }
            };
            const fuelChart = new ApexCharts(document.querySelector("#chart-fuel"), fuelOptions);
            fuelChart.render();

            // Evento de atualização periódica do Livewire
            Livewire.hook('morph.updated', ({ el, component }) => {
                if (component.ephemeral && component.ephemeral.chartData) {
                    const data = component.ephemeral.chartData;
                    lambdaChart.updateSeries([{ data: data.o2 }]);
                    fuelChart.updateSeries([{ data: data.stft }, { data: data.ltft }]);
                }
            });
        });
    </script>
</div>
