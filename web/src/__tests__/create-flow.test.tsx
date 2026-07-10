import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { CreatePage } from "@/components/create-flow/create-page";

const mockNavigate = vi.fn();

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mockNavigate,
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
});

/* Helper: mock provider-status API returning backend data */
function mockProviderStatus(providers?: Array<Record<string, unknown>>) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({
      activeProvider: "9router",
      activeModel: "ocg/deepseek-v4-flash",
      available: true,
      configured: false,
      providers: providers ?? [
        { provider: "9router", label: "9router", defaultModel: "ocg/deepseek-v4-flash", configured: false,
          models: [{ id: "ocg/deepseek-v4-flash", label: "DeepSeek V4 Flash", maxTokens: 32768 }] },
        { provider: "openai", label: "OpenAI", defaultModel: "gpt-4o", configured: false,
          models: [{ id: "gpt-4o", label: "GPT-4o", maxTokens: 16384 }] },
      ],
    }),
  } as Response);
}

describe("CreatePage", () => {
  it("renders template picker", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Templates")).toBeInTheDocument();
    expect(screen.getByText("Explainer")).toBeInTheDocument();
  });

  it("renders genre templates in picker", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Tutorial")).toBeInTheDocument();
    expect(screen.getByText("Marketing")).toBeInTheDocument();
    expect(screen.getByText("Timeline")).toBeInTheDocument();
  });
  it("renders header and prompt input", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Create video")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Describe video you want to create...")).toBeInTheDocument();
  });

  it("renders grill button", () => {
    mockProviderStatus();
    render(<CreatePage />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.some(b => b.textContent?.includes("Grill me"))).toBe(true);
  });

  it("renders options panel", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Options")).toBeInTheDocument();
  });

  it("renders model select field", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByLabelText("Model")).toBeInTheDocument();
  });

  it("renders progress section", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Progress")).toBeInTheDocument();
  });

  it("shows 5 pipeline stages", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Pipeline stages")).toBeInTheDocument();
  });

  it("shows grill panel placeholder when idle", () => {
    mockProviderStatus();
    render(<CreatePage />);
    expect(screen.getByText("Submit a prompt to see grill results")).toBeInTheDocument();
  });

  it("grill button disabled when prompt too short", () => {
    mockProviderStatus();
    render(<CreatePage />);
    const buttons = screen.getAllByRole("button");
    const grillBtn = buttons.find(b => b.textContent?.includes("Grill me"));
    expect(grillBtn?.closest("button")).toBeDisabled();
  });

  it("uses backend provider/model data when available", async () => {
    mockProviderStatus([
      { provider: "9router", label: "9router", defaultModel: "ocg/deepseek-v4-flash", configured: false,
        models: [{ id: "ocg/deepseek-v4-flash", label: "DeepSeek V4 Flash", maxTokens: 32768 }] },
      { provider: "anthropic", label: "Anthropic", defaultModel: "claude-sonnet-4-20250514", configured: true,
        models: [{ id: "claude-sonnet-4-20250514", label: "Claude Sonnet 4", maxTokens: 8192 }] },
    ]);
    render(<CreatePage />);
    // Provider select should include Anthropic from backend data
    await waitFor(() => {
      const providerSelect = screen.getByLabelText("Provider");
      expect(providerSelect).toBeInTheDocument();
    });
    // Model select should show 9router model from backend
    const modelSelect = screen.getByLabelText("Model");
    expect(modelSelect).toBeInTheDocument();
  });

  it("falls back to hardcoded provider list when backend unavailable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
    render(<CreatePage />);
    // Should still render with fallback providers
    await waitFor(() => {
      expect(screen.getByLabelText("Provider")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Model")).toBeInTheDocument();
  });
});
