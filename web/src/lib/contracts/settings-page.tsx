import { useCallback, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DEFAULT_SETTINGS,
  SettingsSchema,
  type ProviderId,
  type Settings,
  type RunOverride,
} from "@/lib/contracts/settings";

/* ─── Constants ─── */

const PROVIDER_LABELS: Record<ProviderId, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  groq: "Groq",
  custom: "Custom",
};

type TabId = "provider" | "queue" | "retry" | "review";

const TAB_META: Record<TabId, { title: string; desc: string }> = {
  provider: {
    title: "Provider & Model",
    desc: "Select LLM provider and model. Per-run temperature and token limits override defaults.",
  },
  queue: {
    title: "Queue",
    desc: "Control concurrency and job queue capacity for render pipeline.",
  },
  retry: {
    title: "Retry",
    desc: "Configure retry budgets for failed scene renders and subagent tasks.",
  },
  review: {
    title: "Review",
    desc: "Set quality gates for automatic review passes. Higher scores = stricter validation.",
  },
};

/* ─── Hook ─── */

function useSettingsForm() {
  const [settings, setSettings] = useState<Settings>(() => {
    try {
      return SettingsSchema.parse(DEFAULT_SETTINGS);
    } catch {
      return DEFAULT_SETTINGS;
    }
  });
  const [override, setOverride] = useState<RunOverride>({ temperature: 0.7, maxTokens: 4096 });
  const [saved, setSaved] = useState(false);

  const patchSettings = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => ({ ...prev, ...patch }));
    setSaved(false);
  }, []);

  const patchOverride = useCallback((patch: Partial<RunOverride>) => {
    setOverride((prev) => ({ ...prev, ...patch }));
    setSaved(false);
  }, []);

  const resetAll = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    setOverride({ temperature: 0.7, maxTokens: 4096 });
    setSaved(false);
  }, []);

  const save = useCallback(async () => {
    SettingsSchema.parse(settings);
    /* ponytail: POST to /api/settings when backend endpoint exists */
    setSaved(true);
    await Promise.resolve();
  }, [settings, override]);

  return { settings, override, patchSettings, patchOverride, resetAll, save, saved };
}

/* ─── Sub-components ─── */

interface ProviderModelTabProps {
  settings: Settings;
  override: RunOverride;
  onSettingsChange: (patch: Partial<Settings>) => void;
  onOverrideChange: (patch: Partial<RunOverride>) => void;
}

function ProviderModelTab({ settings, override, onSettingsChange, onOverrideChange }: ProviderModelTabProps) {
  const activeProvider = settings.providers.find((p) => p.provider === settings.activeProvider);
  const isCustom = settings.activeProvider === "custom";
  const models = activeProvider?.models ?? [];

  const handleProviderChange = (value: string) => {
    const provider = settings.providers.find((p) => p.provider === value);
    if (!provider) return;
    onSettingsChange({ activeProvider: value as ProviderId, activeModel: provider.defaultModel });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-2">
        <Label htmlFor="provider">LLM Provider</Label>
        <select
          id="provider"
          className="flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={settings.activeProvider}
          onChange={(e) => handleProviderChange(e.target.value)}
        >
          {settings.providers.map((p) => (
            <option key={p.provider} value={p.provider}>
              {PROVIDER_LABELS[p.provider as ProviderId] ?? p.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="model">Model</Label>
        <select
          id="model"
          className="flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={settings.activeModel}
          onChange={(e) => onSettingsChange({ activeModel: e.target.value })}
        >
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="apiKey">API Key</Label>
        <Input
          id="apiKey"
          type="password"
          placeholder="sk-\u2026 (stored server-side)"
          value=""
          readOnly
          className="text-muted-foreground"
        />
        <p className="text-xs text-muted-foreground">Key stored server-side. Placeholder confirms provider selection.</p>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="baseUrl">
          Base URL {!isCustom && <span className="text-muted-foreground">(optional)</span>}
        </Label>
        <Input
          id="baseUrl"
          placeholder={isCustom ? "https://your-endpoint.example.com/v1" : "https://api.openai.com/v1"}
          value={isCustom ? (activeProvider?.baseUrl ?? "") : ""}
          readOnly={!isCustom}
          onChange={(e) => {
            if (isCustom) {
              const updated = settings.providers.map((p) =>
                p.provider === "custom" ? { ...p, baseUrl: e.target.value } : p,
              );
              onSettingsChange({ providers: updated });
            }
          }}
        />
      </div>

      <div className="grid gap-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="temperature">Temperature (per-run override)</Label>
          <span className="text-sm text-muted-foreground tabular-nums">{override.temperature.toFixed(2)}</span>
        </div>
        <Slider
          id="temperature"
          min={0}
          max={2}
          step={0.05}
          value={[override.temperature]}
          onValueChange={([v]) => onOverrideChange({ temperature: v ?? 0.7 })}
        />
      </div>

      <div className="grid gap-2">
        <Label htmlFor="maxTokens">Max Tokens (per-run override)</Label>
        <Input
          id="maxTokens"
          type="number"
          min={1}
          max={131072}
          value={override.maxTokens}
          onChange={(e) => onOverrideChange({ maxTokens: Number(e.target.value) || 4096 })}
        />
      </div>
    </div>
  );
}

function QueueTab({ settings, onSettingsChange }: { settings: Settings; onSettingsChange: (p: Partial<Settings>) => void }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="concurrency">Max Concurrency</Label>
          <span className="text-sm text-muted-foreground tabular-nums">{settings.queue.maxConcurrency}</span>
        </div>
        <Slider
          id="concurrency"
          min={1}
          max={32}
          step={1}
          value={[settings.queue.maxConcurrency]}
          onValueChange={([v]) => onSettingsChange({ queue: { ...settings.queue, maxConcurrency: v ?? 4 } })}
        />
        <p className="text-xs text-muted-foreground">Concurrent scene render tasks (1\u201332)</p>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="queueSize">Max Queue Size</Label>
        <Input
          id="queueSize"
          type="number"
          min={1}
          max={500}
          value={settings.queue.maxQueueSize}
          onChange={(e) =>
            onSettingsChange({ queue: { ...settings.queue, maxQueueSize: Number(e.target.value) || 100 } })
          }
        />
        <p className="text-xs text-muted-foreground">Maximum queued jobs before rejection</p>
      </div>
    </div>
  );
}

function RetryTab({ settings, onSettingsChange }: { settings: Settings; onSettingsChange: (p: Partial<Settings>) => void }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-2">
        <Label htmlFor="maxRetries">Max Retries</Label>
        <div className="flex items-center gap-4">
          <Slider
            id="maxRetries"
            min={0}
            max={10}
            step={1}
            value={[settings.retry.maxRetries]}
            onValueChange={([v]) => onSettingsChange({ retry: { ...settings.retry, maxRetries: v ?? 3 } })}
            className="flex-1"
          />
          <span className="w-8 text-right text-sm tabular-nums">{settings.retry.maxRetries}</span>
        </div>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="retryDelay">Retry Delay (ms)</Label>
        <Input
          id="retryDelay"
          type="number"
          min={0}
          max={60000}
          step={100}
          value={settings.retry.retryDelayMs}
          onChange={(e) =>
            onSettingsChange({ retry: { ...settings.retry, retryDelayMs: Number(e.target.value) || 2000 } })
          }
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="grid gap-1">
          <Label htmlFor="backoff">Exponential Backoff</Label>
          <p className="text-xs text-muted-foreground">Double delay on each subsequent retry</p>
        </div>
        <Switch
          id="backoff"
          checked={settings.retry.exponentialBackoff}
          onCheckedChange={(v) => onSettingsChange({ retry: { ...settings.retry, exponentialBackoff: v } })}
        />
      </div>
    </div>
  );
}

function ReviewTab({ settings, onSettingsChange }: { settings: Settings; onSettingsChange: (p: Partial<Settings>) => void }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="l0Score">L0 Min Score</Label>
          <span className="text-sm text-muted-foreground tabular-nums">{settings.review.l0MinScore.toFixed(2)}</span>
        </div>
        <Slider
          id="l0Score"
          min={0}
          max={1}
          step={0.05}
          value={[settings.review.l0MinScore]}
          onValueChange={([v]) => onSettingsChange({ review: { ...settings.review, l0MinScore: v ?? 0.9 } })}
        />
        <p className="text-xs text-muted-foreground">Structural coherence gate</p>
      </div>

      <div className="grid gap-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="l1Score">L1 Min Score</Label>
          <span className="text-sm text-muted-foreground tabular-nums">{settings.review.l1MinScore.toFixed(2)}</span>
        </div>
        <Slider
          id="l1Score"
          min={0}
          max={1}
          step={0.05}
          value={[settings.review.l1MinScore]}
          onValueChange={([v]) => onSettingsChange({ review: { ...settings.review, l1MinScore: v ?? 0.85 } })}
        />
        <p className="text-xs text-muted-foreground">Content accuracy gate</p>
      </div>

      <div className="flex items-center justify-between">
        <div className="grid gap-1">
          <Label htmlFor="coherenceGate">Coherence Gate</Label>
          <p className="text-xs text-muted-foreground">Enable cross-scene coherence validation</p>
        </div>
        <Switch
          id="coherenceGate"
          checked={settings.review.coherenceGateEnabled}
          onCheckedChange={(v) => onSettingsChange({ review: { ...settings.review, coherenceGateEnabled: v } })}
        />
      </div>
    </div>
  );
}

/* ─── Page ─── */

export function SettingsPage() {
  const form = useSettingsForm();
  const [tab, setTab] = useState<TabId>("provider");

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Provider, model, queue, and review configuration</p>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as TabId)} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="provider">Provider &amp; Model</TabsTrigger>
          <TabsTrigger value="queue">Queue</TabsTrigger>
          <TabsTrigger value="retry">Retry</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
        </TabsList>

        <Card>
          <CardHeader>
            <CardTitle>{TAB_META[tab].title}</CardTitle>
            <CardDescription>{TAB_META[tab].desc}</CardDescription>
          </CardHeader>
          <CardContent>
            <TabsContent value="provider" className="mt-0">
              <ProviderModelTab
                settings={form.settings}
                override={form.override}
                onSettingsChange={form.patchSettings}
                onOverrideChange={form.patchOverride}
              />
            </TabsContent>
            <TabsContent value="queue" className="mt-0">
              <QueueTab settings={form.settings} onSettingsChange={form.patchSettings} />
            </TabsContent>
            <TabsContent value="retry" className="mt-0">
              <RetryTab settings={form.settings} onSettingsChange={form.patchSettings} />
            </TabsContent>
            <TabsContent value="review" className="mt-0">
              <ReviewTab settings={form.settings} onSettingsChange={form.patchSettings} />
            </TabsContent>
          </CardContent>
        </Card>
      </Tabs>

      <div className="mt-6 flex items-center justify-end gap-3">
        <Button variant="outline" onClick={form.resetAll}>
          Reset to Defaults
        </Button>
        <Button onClick={form.save}>{form.saved ? "Saved" : "Save Settings"}</Button>
      </div>
    </div>
  );
}
