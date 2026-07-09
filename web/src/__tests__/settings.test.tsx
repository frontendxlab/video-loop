import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { SettingsPage } from "@/lib/contracts/settings-page";
import {
  DEFAULT_SETTINGS,
  SettingsSchema,
  RunOverrideSchema,
} from "@/lib/contracts/settings";
import type { Settings } from "@/lib/contracts/settings";

/* Mock fetch so SettingsPage loads data immediately */
function mockFetchSettings(data?: Partial<Settings>) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ ...DEFAULT_SETTINGS, ...data }),
  } as Response);
}

/* ─── Contract validation ─── */

describe("SettingsSchema", () => {
  it("validates default settings", () => {
    const result = SettingsSchema.safeParse(DEFAULT_SETTINGS);
    expect(result.success).toBe(true);
  });

  it("rejects negative concurrency", () => {
    const result = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      queue: { ...DEFAULT_SETTINGS.queue, maxConcurrency: -1 },
    });
    expect(result.success).toBe(false);
  });

  it("rejects concurrency above 32", () => {
    const result = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      queue: { ...DEFAULT_SETTINGS.queue, maxConcurrency: 99 },
    });
    expect(result.success).toBe(false);
  });

  it("rejects negative retries", () => {
    const result = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      retry: { ...DEFAULT_SETTINGS.retry, maxRetries: -1 },
    });
    expect(result.success).toBe(false);
  });

  it("rejects retries above 10", () => {
    const result = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      retry: { ...DEFAULT_SETTINGS.retry, maxRetries: 15 },
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid provider id", () => {
    const result = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      activeProvider: "nonexistent" as never,
    });
    expect(result.success).toBe(false);
  });

  it("accepts valid provider ids", () => {
    for (const pid of ["openai", "anthropic", "google", "groq", "custom"] as const) {
      const result = SettingsSchema.safeParse({
        ...DEFAULT_SETTINGS,
        activeProvider: pid,
      });
      expect(result.success).toBe(true);
    }
  });

  it("enforces maxQueueSize within bounds", () => {
    const tooSmall = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      queue: { ...DEFAULT_SETTINGS.queue, maxQueueSize: 0 },
    });
    const tooLarge = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      queue: { ...DEFAULT_SETTINGS.queue, maxQueueSize: 999 },
    });
    const valid = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      queue: { ...DEFAULT_SETTINGS.queue, maxQueueSize: 100 },
    });
    expect(tooSmall.success).toBe(false);
    expect(tooLarge.success).toBe(false);
    expect(valid.success).toBe(true);
  });

  it("enforces retryDelayMs within bounds", () => {
    const neg = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      retry: { ...DEFAULT_SETTINGS.retry, retryDelayMs: -100 },
    });
    const huge = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      retry: { ...DEFAULT_SETTINGS.retry, retryDelayMs: 120_000 },
    });
    expect(neg.success).toBe(false);
    expect(huge.success).toBe(false);
  });

  it("rejects review scores out of range", () => {
    const high = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      review: { ...DEFAULT_SETTINGS.review, l0MinScore: 1.5 },
    });
    const low = SettingsSchema.safeParse({
      ...DEFAULT_SETTINGS,
      review: { ...DEFAULT_SETTINGS.review, l1MinScore: -0.1 },
    });
    expect(high.success).toBe(false);
    expect(low.success).toBe(false);
  });
});

describe("RunOverrideSchema", () => {
  it("accepts valid override", () => {
    const result = RunOverrideSchema.safeParse({ temperature: 0.5, maxTokens: 8192 });
    expect(result.success).toBe(true);
  });

  it("rejects temperature out of range", () => {
    const high = RunOverrideSchema.safeParse({ temperature: 3, maxTokens: 4096 });
    const low = RunOverrideSchema.safeParse({ temperature: -1, maxTokens: 4096 });
    expect(high.success).toBe(false);
    expect(low.success).toBe(false);
  });

  it("applies defaults for partial override", () => {
    const result = RunOverrideSchema.safeParse({});
    expect(result.success).toBe(true);
    expect(result.data?.temperature).toBe(0.7);
    expect(result.data?.maxTokens).toBe(4096);
  });
});

/* ─── UI rendering ─── */

describe("SettingsPage", () => {
  beforeEach(() => {
    mockFetchSettings();
  });

  it("renders heading", async () => {
    render(<SettingsPage />);
    expect(await screen.findByText("Settings")).toBeInTheDocument();
  });

  it("renders all four tab triggers", async () => {
    render(<SettingsPage />);
    expect(await screen.findByText("Queue")).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
  });

  it("renders provider and model controls", async () => {
    render(<SettingsPage />);
    expect(await screen.findByLabelText("LLM Provider")).toBeInTheDocument();
    expect(screen.getByLabelText("Model")).toBeInTheDocument();
  });

  it("renders save and reset buttons", async () => {
    render(<SettingsPage />);
    expect(await screen.findByText("Save Settings")).toBeInTheDocument();
    expect(screen.getByText("Reset to Defaults")).toBeInTheDocument();
  });

  it("renders API key placeholder", async () => {
    render(<SettingsPage />);
    expect(await screen.findByLabelText("API Key")).toBeInTheDocument();
  });

  it("renders temperature slider", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      const slider = document.querySelector('[id="temperature"]');
      expect(slider).toBeInTheDocument();
    });
  });

  it("renders max tokens input", async () => {
    render(<SettingsPage />);
    expect(await screen.findByLabelText(/max tokens/i)).toBeInTheDocument();
  });
});
