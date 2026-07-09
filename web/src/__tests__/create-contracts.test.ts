import { describe, it, expect } from "vitest";
import {
  CreateJobRequestSchema, GrillResultSchema, RecipeSchema,
  DEFAULT_OPTIONS, CREATE_STAGES, RECIPE_PRESETS,
} from "@/contracts/create";

describe("CreateJobRequestSchema", () => {
  it("validates minimal request", () => expect(CreateJobRequestSchema.safeParse({ prompt: "Explain Kubernetes architecture", options: DEFAULT_OPTIONS }).success).toBe(true));
  it("rejects prompt under 10 chars", () => expect(CreateJobRequestSchema.safeParse({ prompt: "Hi", options: DEFAULT_OPTIONS }).success).toBe(false));
  it("applies defaults for missing options", () => {
    const r = CreateJobRequestSchema.safeParse({ prompt: "A video about testing defaults", options: {} });
    expect(r.success).toBe(true);
    if (r.success) { expect(r.data.options.fps).toBe(30); expect(r.data.options.voice).toBe("alba"); }
  });
  it("accepts optional recipeId", () => {
    const r = CreateJobRequestSchema.safeParse({ prompt: "Test recipe in request", options: DEFAULT_OPTIONS, recipeId: "hero-intro" });
    expect(r.success).toBe(true);
    if (r.success) expect(r.data.recipeId).toBe("hero-intro");
  });
});

describe("GrillResultSchema", () => {
  it("validates grill result", () => expect(GrillResultSchema.safeParse({ refinedPrompt: "test", suggestedScenes: [{ kind: "title", title: "Intro", description: "Opening", reasoning: "Standard" }], missingDetails: [], confidence: 0.85 }).success).toBe(true));
});

describe("CREATE_STAGES", () => {
  it("has 5 stages", () => { expect(CREATE_STAGES).toHaveLength(5); expect(CREATE_STAGES[0].id).toBe("grill"); expect(CREATE_STAGES[4].id).toBe("review"); });
});

describe("RecipeSchema", () => {
  it("validates a recipe object", () => {
    const r = RecipeSchema.safeParse(RECIPE_PRESETS[0]);
    expect(r.success).toBe(true);
  });
  it("requires id and name", () => {
    expect(RecipeSchema.safeParse({}).success).toBe(false);
  });
});

describe("RECIPE_PRESETS", () => {
  it("has at least 9 predefined recipes", () => {
    expect(RECIPE_PRESETS.length).toBeGreaterThanOrEqual(9);
  });
  it("every recipe has required fields", () => {
    for (const r of RECIPE_PRESETS) {
      expect(r.id).toBeTruthy();
      expect(r.name).toBeTruthy();
      expect(r.sceneKind).toBeTruthy();
      expect(r.preferredEngine).toBeTruthy();
      expect(Array.isArray(r.tags)).toBe(true);
      expect(Array.isArray(r.allowedInputs)).toBe(true);
    }
  });
  it("has unique ids", () => {
    const ids = RECIPE_PRESETS.map(r => r.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
  it("every allowed input has key and type", () => {
    for (const r of RECIPE_PRESETS) {
      for (const inp of r.allowedInputs) {
        expect(inp.key).toBeTruthy();
        expect(["string", "number", "boolean", "array"]).toContain(inp.type);
      }
    }
  });
  it("contains hero-intro recipe", () => {
    expect(RECIPE_PRESETS.find(r => r.id === "hero-intro")).toBeTruthy();
  });
  it("contains map3d recipe", () => {
    expect(RECIPE_PRESETS.find(r => r.id === "map3d")).toBeTruthy();
  });
});
