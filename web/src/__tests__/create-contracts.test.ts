import { describe, it, expect } from "vitest";
import { CreateJobRequestSchema, GrillResultSchema, DEFAULT_OPTIONS, CREATE_STAGES } from "@/contracts/create";

describe("CreateJobRequestSchema", () => {
  it("validates minimal request", () => expect(CreateJobRequestSchema.safeParse({ prompt: "Explain Kubernetes architecture", options: DEFAULT_OPTIONS }).success).toBe(true));
  it("rejects prompt under 10 chars", () => expect(CreateJobRequestSchema.safeParse({ prompt: "Hi", options: DEFAULT_OPTIONS }).success).toBe(false));
  it("applies defaults for missing options", () => {
    const r = CreateJobRequestSchema.safeParse({ prompt: "A video about testing defaults", options: {} });
    expect(r.success).toBe(true);
    if (r.success) { expect(r.data.options.fps).toBe(30); expect(r.data.options.voice).toBe("alba"); }
  });
});

describe("GrillResultSchema", () => {
  it("validates grill result", () => expect(GrillResultSchema.safeParse({ refinedPrompt: "test", suggestedScenes: [{ kind: "title", title: "Intro", description: "Opening", reasoning: "Standard" }], missingDetails: [], confidence: 0.85 }).success).toBe(true));
});

describe("CREATE_STAGES", () => {
  it("has 5 stages", () => { expect(CREATE_STAGES).toHaveLength(5); expect(CREATE_STAGES[0].id).toBe("grill"); expect(CREATE_STAGES[4].id).toBe("review"); });
});
