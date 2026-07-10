import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CreateOptions, Voice } from "@/contracts/create";
import { useProviderModels } from "@/hooks/useProviderModels";
import type { ProviderOption, ModelOption } from "@/hooks/useProviderModels";

const VOICES: { value: Voice; label: string }[] = [
  { value: "alba", label: "Alba" }, { value: "alice", label: "Alice" },
  { value: "bella", label: "Bella" }, { value: "maria", label: "Maria" },
  { value: "nora", label: "Nora" }, { value: "sara", label: "Sara" },
];

/* ─── Fallback when backend unavailable ─── */

const FALLBACK_PROVIDERS: ProviderOption[] = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
  { value: "groq", label: "Groq" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "9router", label: "9router" },
  { value: "custom", label: "Custom" },
];

const FALLBACK_MODELS: Record<string, ModelOption[]> = {
  openai:    [{ value: "gpt-4o", label: "GPT-4o" }, { value: "gpt-4o-mini", label: "GPT-4o Mini" }],
  anthropic: [{ value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4" }],
  google:    [{ value: "gemini-2.0-flash", label: "Gemini 2.0 Flash" }],
  groq:      [{ value: "llama-3.3-70b", label: "Llama 3.3 70B" }],
  deepseek:  [{ value: "deepseek-chat", label: "DeepSeek Chat" }],
  "9router": [
    { value: "ocg/deepseek-v4-flash", label: "DeepSeek V4 Flash" },
    { value: "ocg/deepseek-v4-flash:free", label: "DeepSeek V4 Flash Free" },
    { value: "ocg/deepseek-v4-pro", label: "DeepSeek V4 Pro" },
    { value: "oc/deepseek-v4-flash-free", label: "OpenCode Zen" },
    { value: "oc/big-pickle", label: "Big Pickle" },
  ],
  custom:    [{ value: "custom-model", label: "Custom Model" }],
};

/* ─── Component ─── */

interface CreateOptionsProps {
  options: CreateOptions;
  onChange: (options: CreateOptions) => void;
  disabled?: boolean;
  className?: string;
}

export function CreateOptionsPanel({ options, onChange, disabled, className }: CreateOptionsProps) {
  const { providers, modelsByProvider } = useProviderModels();

  // Use API data if available, fall back to hardcoded maps
  const actualProviders = providers.length > 0 ? providers : FALLBACK_PROVIDERS;
  const actualModelsByProvider = Object.keys(modelsByProvider).length > 0
    ? modelsByProvider
    : FALLBACK_MODELS;

  const set = <K extends keyof CreateOptions>(key: K, value: CreateOptions[K]) =>
    onChange({ ...options, [key]: value });

  const availableModels = actualModelsByProvider[options.provider] ?? actualModelsByProvider.custom ?? [];

  const handleProviderChange = (v: string) => {
    const models = actualModelsByProvider[v] ?? actualModelsByProvider.custom ?? [];
    const defaultModel = models[0]?.value ?? "custom-model";
    onChange({ ...options, provider: v as CreateOptions["provider"], model: defaultModel });
  };

  return (
    <Card className={cn("", className)}>
      <CardContent className="space-y-4 p-4">
        <h4 className="text-sm font-medium">Options</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="voice">Voice</Label>
            <Select value={options.voice} onValueChange={(v) => set("voice", v as Voice)} disabled={disabled}>
              <SelectTrigger id="voice"><SelectValue /></SelectTrigger>
              <SelectContent>{VOICES.map(v => <SelectItem key={v.value} value={v.value}>{v.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select value={options.provider} onValueChange={handleProviderChange} disabled={disabled}>
              <SelectTrigger id="provider"><SelectValue /></SelectTrigger>
              <SelectContent>{actualProviders.map(p => <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select value={options.model} onValueChange={(v) => set("model", v)} disabled={disabled}>
              <SelectTrigger id="model"><SelectValue /></SelectTrigger>
              <SelectContent>{availableModels.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="maxDuration">Max duration (s)</Label>
            <Input id="maxDuration" type="number" min={30} max={600} value={options.maxDuration}
              onChange={(e) => set("maxDuration", Number(e.target.value))} disabled={disabled} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="fps">FPS</Label>
            <Select value={String(options.fps)} onValueChange={(v) => set("fps", Number(v))} disabled={disabled}>
              <SelectTrigger id="fps"><SelectValue /></SelectTrigger>
              <SelectContent>{["24","30","60"].map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
