<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-xl font-bold text-white tracking-wide">Histórico de Sessões de Diagnóstico</h1>
            <p class="text-xs text-slate-400">Consulte laudos, telemetrias gravadas e códigos de falha de diagnósticos anteriores.</p>
        </div>
        <a href="/" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-600/30 transition">
            + Nova Sessão / Dashboard
        </a>
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
        <table class="w-full text-left text-sm text-slate-300">
            <thead class="bg-slate-950 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                    <th class="px-6 py-4">Data / Hora</th>
                    <th class="px-6 py-4">Veículo</th>
                    <th class="px-6 py-4">Porta / Protocolo</th>
                    <th class="px-6 py-4">Pontos de Telemetria</th>
                    <th class="px-6 py-4">DTCs (Falhas)</th>
                    <th class="px-6 py-4 text-right">Ações</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
                @forelse ($sessions as $session)
                    <tr class="hover:bg-slate-800/40 transition">
                        <td class="px-6 py-4 font-mono text-xs text-slate-300">
                            {{ $session->started_at ? $session->started_at->format('d/m/Y H:i:s') : '--' }}
                        </td>
                        <td class="px-6 py-4">
                            <span class="font-semibold text-white">
                                {{ $session->vehicle ? $session->vehicle->make . ' ' . $session->vehicle->model : 'Ford New Fiesta 1.5' }}
                            </span>
                            <span class="block text-[11px] text-slate-500">
                                {{ $session->vehicle ? $session->vehicle->engine . ' (' . $session->vehicle->fuel_type . ')' : '1.5 Sigma Flex' }}
                            </span>
                        </td>
                        <td class="px-6 py-4 font-mono text-xs text-slate-400">
                            {{ $session->port ?? 'Virtual' }}
                            <span class="block text-[10px] text-slate-500">{{ $session->protocol ?? 'CAN 11/500' }}</span>
                        </td>
                        <td class="px-6 py-4">
                            <span class="px-2.5 py-1 rounded bg-slate-800 text-xs font-mono text-indigo-300">
                                {{ $session->frames_count }} frames
                            </span>
                        </td>
                        <td class="px-6 py-4">
                            @if ($session->dtcs_count > 0)
                                <span class="px-2.5 py-1 rounded bg-rose-500/20 text-xs font-bold text-rose-400">
                                    {{ $session->dtcs_count }} DTC(s)
                                </span>
                            @else
                                <span class="px-2.5 py-1 rounded bg-emerald-500/20 text-xs font-semibold text-emerald-400">
                                    Nenhuma
                                </span>
                            @endif
                        </td>
                        <td class="px-6 py-4 text-right space-x-2">
                            <a href="/report/{{ $session->id }}" target="_blank"
                               class="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded text-xs font-medium transition inline-flex items-center space-x-1">
                                <span>📄 Laudo / Imprimir</span>
                            </a>
                            <button wire:click="deleteSession('{{ $session->id }}')" 
                                    wire:confirm="Tem certeza que deseja excluir esta sessão e todo seu histórico?"
                                    class="px-2 py-1.5 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 rounded text-xs font-medium transition">
                                ✕
                            </button>
                        </td>
                    </tr>
                @empty
                    <tr>
                        <td colspan="6" class="px-6 py-12 text-center text-slate-500 text-sm">
                            Nenhuma sessão de diagnóstico registrada ainda. Conecte o ELM327 ou inicie o simulador.
                        </td>
                    </tr>
                @endforelse
            </tbody>
        </table>
    </div>
</div>
