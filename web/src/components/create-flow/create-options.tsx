import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CreateOptions, Voice } from "@/contracts/create";

const VOICES: { value: Voice; label: string }[] = [
  { value: "alba", label: "Alba" }, { value: "alice", label: "Alice" },
  { value: "bella", label: "Bella" }, { value: "maria", label: "Maria" },
  { value: "nora", label: "Nora" }, { value: "sara", label: "Sara" },
];

const PROVIDERS = [
  { value: "openai", label: "OpenAI" }, { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" }, { value: "deepseek", label: "DeepSeek" },
  { value: "custom", label: "Custom" },
];

interface CreateOptionsProps {
  options: CreateOptions;
  onChange: (options: CreateOptions) => void;
  disabled?: boolean;
  className?: string;
}

export function CreateOptionsPanel({ options, onChange, disabled, className }: CreateOptionsProps) {
  const set = <K extends keyof CreateOptions>(key: K, value: CreateOptions[K]) =>
    onChange({ ...options, [key]: value });

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
            <Select value={options.provider} onValueChange={(v) => set("provider", v as CreateOptions["provider"])} disabled={disabled}>
              <SelectTrigger id="provider"><SelectValue /></SelectTrigger>
              <SelectContent>{PROVIDERS.map(p => <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>)}</SelectContent>
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
