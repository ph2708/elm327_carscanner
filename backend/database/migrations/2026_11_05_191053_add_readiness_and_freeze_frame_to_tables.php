<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('diagnostic_sessions', function (Blueprint $table) {
            $table->json('readiness_monitors')->nullable()->after('supported_pids');
            $table->boolean('mil_active')->default(false)->after('readiness_monitors');
            $table->integer('dtc_count')->default(0)->after('mil_active');
        });

        Schema::table('session_dtcs', function (Blueprint $table) {
            $table->string('description')->nullable()->after('type');
        });
    }

    public function down(): void
    {
        Schema::table('session_dtcs', function (Blueprint $table) {
            $table->dropColumn('description');
        });

        Schema::table('diagnostic_sessions', function (Blueprint $table) {
            $table->dropColumn(['readiness_monitors', 'mil_active', 'dtc_count']);
        });
    }
};
