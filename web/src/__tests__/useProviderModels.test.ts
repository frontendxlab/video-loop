import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useProviderModels } from "@/hooks/useProviderModels";

beforeEach(() => {
  vi.restoreAllMocks();
});

const MOCK_STATUS_RESPONSE = {
  activeProvider: "9router",
  activeModel: "ocg/deepseek-v4-flash",
  available: true,
  configured: false,
  providers: [
    {
      provider: "9router",
      label: "9router",
      defaultModel: "ocg/deepseek-v4-flash",
      configured: false,
      models: [
        { id: "ocg/deepseek-v4-flash", label: "DeepSeek V4 Flash", maxTokens: 32768 },
        { id: "ocg/deepseek-v4-flash:free", label: "DeepSeek V4 Flash Free", maxTokens: 8192 },
      ],
    },
    {
      provider: "openai",
      label: "OpenAI",
      defaultModel: "gpt-4o",
      configured: false,
      models: [
        { id: "gpt-4o", label: "GPT-4o", maxTokens: 16384 },
        { id: "gpt-4o-mini", label: "GPT-4o Mini", maxTokens: 16384 },
      ],
    },
  ],
};

describe("useProviderModels", () => {
  it("returns backend provider/models on successful fetch", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_STATUS_RESPONSE),
    } as Response);

    const { result } = renderHook(() => useProviderModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.providers).toHaveLength(2);
    expect(result.current.providers[0].value).toBe("9router");
    expect(result.current.providers[0].label).toBe("9router");
    expect(result.current.providers[1].value).toBe("openai");
    expect(result.current.modelsByProvider["9router"]).toHaveLength(2);
    expect(result.current.modelsByProvider["9router"][0].value).toBe("ocg/deepseek-v4-flash");
    expect(result.current.error).toBeNull();
  });

  it("falls back to DEFAULT_SETTINGS on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useProviderModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    // Fallback should have all providers from DEFAULT_SETTINGS
    expect(result.current.providers.length).toBeGreaterThanOrEqual(6);
    expect(result.current.providers.some((p) => p.value === "9router")).toBe(true);
    expect(result.current.providers.some((p) => p.value === "custom")).toBe(true);
    expect(result.current.modelsByProvider["9router"]).toBeDefined();
    expect(result.current.error).toBe("Network error");
  });

  it("falls back on HTTP error status", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
    } as Response);

    const { result } = renderHook(() => useProviderModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.providers.length).toBeGreaterThanOrEqual(6);
    expect(result.current.error).toContain("HTTP 500");
  });

  it("stays on fallback when backend returns empty providers array", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ...MOCK_STATUS_RESPONSE, providers: [] }),
    } as Response);

    const { result } = renderHook(() => useProviderModels());

    await waitFor(() => expect(result.current.loading).toBe(false));

    // Should keep the initial fallback (DEFAULT_SETTINGS)
    expect(result.current.providers.length).toBeGreaterThanOrEqual(6);
  });

  it("starts with loading true", () => {
    // Don't resolve the fetch so it stays in loading state
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useProviderModels());

    expect(result.current.loading).toBe(true);
    // Should already have fallback data available
    expect(result.current.providers.length).toBeGreaterThanOrEqual(6);
  });
});
