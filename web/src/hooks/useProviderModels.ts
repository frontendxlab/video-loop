import { useState, useEffect } from "react";
import { DEFAULT_SETTINGS } from "@/lib/contracts/settings";

export interface ProviderOption {
  value: string;
  label: string;
}

export interface ModelOption {
  value: string;
  label: string;
  maxTokens?: number;
}

export interface ProviderModelsResult {
  providers: ProviderOption[];
  modelsByProvider: Record<string, ModelOption[]>;
  loading: boolean;
  error: string | null;
}

/** Map settings provider config to flat provider+model options used by selects. */
function toOptions(
  providers: typeof DEFAULT_SETTINGS.providers,
): Pick<ProviderModelsResult, "providers" | "modelsByProvider"> {
  return {
    providers: providers.map((p) => ({ value: p.provider, label: p.label })),
    modelsByProvider: Object.fromEntries(
      providers.map((p) => [
        p.provider,
        p.models.map((m) => ({ value: m.id, label: m.label, maxTokens: m.maxTokens })),
      ]),
    ),
  };
}

/**
 * Fetch provider/model lists from backend `/api/settings/provider-status`.
 * Falls back to `DEFAULT_SETTINGS.providers` if backend unavailable.
 * Used by create-flow and settings UI to show dynamic provider/model lists.
 */
export function useProviderModels(): ProviderModelsResult {
  const [result, setResult] = useState<ProviderModelsResult>({
    ...toOptions(DEFAULT_SETTINGS.providers),
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    fetch("/api/settings/provider-status")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<{
          providers: Array<{
            provider: string;
            label: string;
            defaultModel: string;
            models: Array<{ id: string; label: string; maxTokens: number }>;
          }>;
        }>;
      })
      .then((data) => {
        if (cancelled) return;
        const providers = data.providers ?? [];
        if (providers.length === 0) {
          // Empty array from backend — stay on fallback
          setResult((prev) => ({ ...prev, loading: false }));
          return;
        }
        setResult({
          ...toOptions(providers),
          loading: false,
          error: null,
        });
      })
      .catch((err: Error) => {
        if (cancelled) return;
        console.warn("Provider status fetch failed, using defaults:", err.message);
        // Keep fallback (already set as initial state)
        setResult((prev) => ({ ...prev, loading: false, error: err.message }));
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return result;
}
