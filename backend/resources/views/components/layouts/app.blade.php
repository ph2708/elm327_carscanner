<!DOCTYPE html>
<html lang="pt-BR" class="h-full bg-slate-950 text-slate-100">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AutoScan BR — Diagnóstico & Telemetria Automotiva</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    @livewireStyles
</head>
<body class="h-full flex flex-col font-sans antialiased bg-slate-950">
    <nav class="bg-slate-900 border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">🚗</span>
                    <a href="/" class="text-lg font-black tracking-wider text-white">AUTOSCAN <span class="text-indigo-500">BR</span></a>
                    <span class="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Pro Edition</span>
                </div>
                <div class="flex space-x-4 text-sm font-medium">
                    <a href="/" class="px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">Dashboard</a>
                    <a href="/settings" class="px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">IA & Configurações</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-1">
        {{ $slot }}
    </main>

    @livewireScripts
</body>
</html>

