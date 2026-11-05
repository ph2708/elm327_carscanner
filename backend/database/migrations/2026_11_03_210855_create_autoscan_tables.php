<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // 1. Veículos cadastrados
        Schema::create('vehicles', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('vin', 17)->nullable()->index();
            $table->string('make');                  // ex: Ford
            $table->string('model');                 // ex: New Fiesta
            $table->integer('year');                 // ex: 2014
            $table->string('engine');                // ex: 1.5 Sigma 16V
            $table->string('fuel_type')->default('Flex'); // Flex, Gasolina, Etanol
            $table->json('metadata')->nullable();    // Capacidades, limites nominais
            $table->timestamps();
        });

        // 2. Sessões de Diagnóstico
        Schema::create('diagnostic_sessions', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('vehicle_id')->nullable()->constrained('vehicles')->nullOnDelete();
            $table->string('status')->default('ACTIVE'); // ACTIVE, COMPLETED, INTERRUPTED
            $table->string('port')->nullable();
            $table->string('protocol')->nullable();
            $table->string('adapter_version')->nullable();
            $table->json('supported_pids')->nullable();
            $table->timestamp('started_at')->useCurrent();
            $table->timestamp('ended_at')->nullable();
            $table->timestamps();
        });

        // 3. Telemetria em tempo real
        Schema::create('telemetry_frames', function (Blueprint $table) {
            $table->id();
            $table->foreignUuid('session_id')->constrained('diagnostic_sessions')->cascadeOnDelete();
            $table->timestamp('captured_at')->useCurrent();
            $table->float('rpm')->nullable();
            $table->float('speed')->nullable();
            $table->float('coolant_temp')->nullable();
            $table->float('intake_temp')->nullable();
            $table->float('map_kpa')->nullable();
            $table->float('maf_gs')->nullable();
            $table->float('tps')->nullable();
            $table->float('o2_b1s1')->nullable();
            $table->float('stft_b1')->nullable();
            $table->float('ltft_b1')->nullable();
            $table->json('extra_pids')->nullable();

            $table->index(['session_id', 'captured_at']);
        });

        // 4. Códigos de falha DTC detectados
        Schema::create('session_dtcs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('session_id')->constrained('diagnostic_sessions')->cascadeOnDelete();
            $table->string('code', 10);              // ex: P0171
            $table->string('type')->default('STORED'); // STORED, PENDING, PERMANENT
            $table->json('freeze_frame')->nullable();
            $table->timestamps();
        });

        // 5. Laudos e Pareceres de Diagnóstico (Motor de Regras + IA Gemini)
        Schema::create('diagnostic_findings', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('session_id')->constrained('diagnostic_sessions')->cascadeOnDelete();
            $table->string('source')->default('RULE_ENGINE'); // RULE_ENGINE ou GEMINI_AI
            $table->string('symptom');
            $table->json('supporting_data');
            $table->json('possible_causes');
            $table->integer('confidence_percent')->default(80);
            $table->text('recommended_tests');
            $table->text('expected_outcome');
            $table->timestamps();
        });

        // 6. Configurações Globais (API Keys Gemini, Parâmetros)
        Schema::create('system_settings', function (Blueprint $table) {
            $table->string('key')->primary();
            $table->text('value')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('system_settings');
        Schema::dropIfExists('diagnostic_findings');
        Schema::dropIfExists('session_dtcs');
        Schema::dropIfExists('telemetry_frames');
        Schema::dropIfExists('diagnostic_sessions');
        Schema::dropIfExists('vehicles');
    }
};
