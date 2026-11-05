<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\SystemSetting;
use App\Services\GeminiDiagnosticService;

class Settings extends Component
{
    public string $gemini_api_key = '';
    public string $gemini_model = 'gemini-1.5-flash';
    public ?string $feedbackMessage = null;
    public bool $isSuccess = false;

    public function mount()
    {
        $this->gemini_api_key = SystemSetting::get('gemini_api_key', '');
        $this->gemini_model = SystemSetting::get('gemini_model', 'gemini-1.5-flash');
    }

    public function save()
    {
        SystemSetting::set('gemini_api_key', trim($this->gemini_api_key));
        SystemSetting::set('gemini_model', $this->gemini_model);

        $this->isSuccess = true;
        $this->feedbackMessage = 'Configurações salvas com sucesso!';
    }

    public function testGemini(GeminiDiagnosticService $service)
    {
        $key = trim($this->gemini_api_key);
        if (empty($key)) {
            $this->isSuccess = false;
            $this->feedbackMessage = 'Informe uma chave de API antes de testar.';
            return;
        }

        $res = $service->testConnection($key);
        $this->isSuccess = $res['success'];
        $this->feedbackMessage = $res['message'];

        if ($res['success']) {
            SystemSetting::set('gemini_api_key', $key);
        }
    }

    public function render()
    {
        return view('livewire.settings');
    }
}
