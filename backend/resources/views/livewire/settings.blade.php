<div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl">
        <div class="flex items-center space-x-3 mb-6">
            <div class="p-3 bg-indigo-600/20 text-indigo-400 rounded-lg">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
            </div>
            <div>
                <h2 class="text-xl font-bold text-white">Inteligência Artificial & APIs</h2>
                <p class="text-sm text-slate-400">Configure a chave de API do Google Gemini para diagnósticos e laudos técnicos detalhados.</p>
            </div>
        </div>

        @if ($feedbackMessage)
            <div class="mb-6 p-4 rounded-lg text-sm {{ $isSuccess ? 'bg-emerald-950/50 border border-emerald-500/40 text-emerald-300' : 'bg-rose-950/50 border border-rose-500/40 text-rose-300' }}">
                <div class="flex items-center space-x-2">
                    <span>{{ $isSuccess ? '✓' : '⚠' }}</span>
                    <span>{{ $feedbackMessage }}</span>
                </div>
            </div>
        @endif

        <form wire:submit="save" class="space-y-6">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">Google Gemini API Key</label>
                <div class="relative">
                    <input type="password" wire:model="gemini_api_key" placeholder="AIzaSy..." 
                           class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm">
                </div>
                <p class="mt-1 text-xs text-slate-400">
                    Você pode obter sua chave gratuitamente no <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-indigo-400 underline hover:text-indigo-300">Google AI Studio</a>.
                </p>
            </div>

            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">Modelo Gemini</label>
                <select wire:model="gemini_model" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Ultrarrápido, ideal para diagnósticos em tempo real)</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Raciocínio complexo para falhas intermitentes)</option>
                </select>
            </div>

            <div class="pt-4 border-t border-slate-800 flex items-center justify-between">
                <button type="button" wire:click="testGemini" wire:loading.attr="disabled"
                        class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition flex items-center space-x-2">
                    <span wire:loading.remove wire:target="testGemini">⚡ Testar Conexão</span>
                    <span wire:loading wire:target="testGemini">Verificando...</span>
                </button>

                <button type="submit" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition shadow-lg shadow-indigo-600/30">
                    Salvar Alterações
                </button>
            </div>
        </form>

        <div class="mt-8 pt-6 border-t border-slate-800">
            <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">Suporte OpenAI / ChatGPT</h3>
            <p class="text-xs text-slate-400 leading-relaxed">
                O AutoScan BR já possui a arquitetura modular pronta para receber chaves da OpenAI. Atualmente o provedor ativo e recomendado para diagnósticos é o <strong>Google Gemini</strong> devido à alta velocidade e excelente cota gratuita.
            </p>
        </div>
    </div>
</div>
