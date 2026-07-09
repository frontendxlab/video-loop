import { describe, it, expect, vi, beforeEach } from "vitest";
import { grillPrompt, createJob } from "@/api/jobs";
import { DEFAULT_OPTIONS } from "@/contracts/create";

const MOCK_GRILL_RESULT = {
  refinedPrompt: "Create a detailed technical video about: Kubernetes architecture.",
  suggestedScenes: [
    { kind: "title", title: "Title", description: "Opening title card with topic", reasoning: "Establishes video topic" },
    { kind: "code", title: "Code Example", description: "Live code walkthrough", reasoning: "Visual code explanation" },
    { kind: "outro", title: "Summary", description: "Recap and next steps", reasoning: "Closing summary" },
  ],
  missingDetails: ["Target audience not specified"],
  confidence: 0.72,
};

const MOCK_CREATE_RESPONSE = {
  jobId: "job_abc123def456",
  status: "queued",
  grillResult: MOCK_GRILL_RESULT,
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("grillPrompt", () => {
  it("calls POST /api/jobs/grill with prompt and options", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_GRILL_RESULT),
    } as Response);

    const result = await grillPrompt("Explain Kubernetes architecture", DEFAULT_OPTIONS);

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/jobs/grill",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: expect.stringContaining("Kubernetes"),
      }),
    );
    expect(result).toEqual(MOCK_GRILL_RESULT);
  });

  it("throws on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 422,
      text: () => Promise.resolve("Validation error"),
    } as Response);

    await expect(grillPrompt("Explain Kubernetes", DEFAULT_OPTIONS)).rejects.toThrow("Grill failed");
  });

  it("validates response shape with Zod schema", async () => {
    const badData = { refinedPrompt: "", suggestedScenes: "not-an-array" };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(badData),
    } as Response);

    await expect(grillPrompt("Explain Kubernetes", DEFAULT_OPTIONS)).rejects.toThrow();
  });
});

describe("createJob", () => {
  it("calls POST /api/jobs with prompt and options", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_CREATE_RESPONSE),
    } as Response);

    const result = await createJob("Explain Kubernetes architecture", DEFAULT_OPTIONS);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/jobs",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("Kubernetes"),
      }),
    );
    expect(result.jobId).toBe("job_abc123def456");
    expect(result.status).toBe("queued");
    expect(result.grillResult.confidence).toBe(0.72);
  });

  it("throws on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve("Server error"),
    } as Response);

    await expect(createJob("Explain Kubernetes", DEFAULT_OPTIONS)).rejects.toThrow("Create job failed");
  });
});
