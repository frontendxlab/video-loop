import { describe, it, expect } from "vitest";
import {
  CreateJobRequestSchema, CreateOptionsSchema, GrillResultSchema, RecipeSchema,
  DEFAULT_OPTIONS, CREATE_STAGES, RECIPE_PRESETS,
} from "@/contracts/create";

describe("CreateOptionsSchema", () => {
  it("accepts 9router as provider", () => {
    const r = CreateOptionsSchema.safeParse({ provider: "9router", model: "ocg/deepseek-v4-flash" });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.provider).toBe("9router");
      expect(r.data.model).toBe("ocg/deepseek-v4-flash");
    }
  });

  it("defaults to 9router and ocg/deepseek-v4-flash model", () => {
    const r = CreateOptionsSchema.safeParse({});
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.provider).toBe("9router");
      expect(r.data.model).toBe("ocg/deepseek-v4-flash");
    }
  });

  it("accepts 9router free tier model", () => {
    const r = CreateOptionsSchema.safeParse({ provider: "9router", model: "ocg/deepseek-v4-flash:free" });
    expect(r.success).toBe(true);
  });

  it("rejects invalid provider", () => {
    const r = CreateOptionsSchema.safeParse({ provider: "invalid-provider" });
    expect(r.success).toBe(false);
  });
});

describe("DEFAULT_OPTIONS", () => {
  it("defaults provider to 9router", () => {
    expect(DEFAULT_OPTIONS.provider).toBe("9router");
    expect(DEFAULT_OPTIONS.model).toBe("ocg/deepseek-v4-flash");
  });
});

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

describe("RECIPE_PRESETS — showcase metadata", () => {
  it("every recipe has useCases", () => {
    for (const r of RECIPE_PRESETS) {
      expect(Array.isArray(r.useCases)).toBe(true);
      expect(r.useCases.length).toBeGreaterThanOrEqual(2);
    }
  });
  it("every recipe has motionHints with entrance and exit", () => {
    for (const r of RECIPE_PRESETS) {
      expect(r.motionHints).toBeDefined();
      expect(typeof r.motionHints.entrance).toBe("string");
      expect(r.motionHints.entrance.length).toBeGreaterThan(5);
      expect(typeof r.motionHints.exit).toBe("string");
      expect(r.motionHints.exit.length).toBeGreaterThan(5);
    }
  });
  it("every recipe has reviewHints", () => {
    for (const r of RECIPE_PRESETS) {
      expect(Array.isArray(r.reviewHints)).toBe(true);
      expect(r.reviewHints.length).toBeGreaterThanOrEqual(1);
    }
  });
  it("every recipe has engineBadges", () => {
    for (const r of RECIPE_PRESETS) {
      expect(Array.isArray(r.engineBadges)).toBe(true);
      expect(r.engineBadges.length).toBeGreaterThanOrEqual(1);
      for (const b of r.engineBadges) {
        expect(typeof b.engine).toBe("string");
        expect(typeof b.label).toBe("string");
      }
    }
  });
  it("3d-ranking has two engine badges (primary + fallback)", () => {
    const recipe = RECIPE_PRESETS.find(r => r.id === "3d-ranking");
    expect(recipe).toBeDefined();
    expect(recipe!.engineBadges.length).toBe(2);
    expect(recipe!.engineBadges[0].engine).toBe("remotion");
    expect(recipe!.engineBadges[1].engine).toBe("manim");
  });
  it("useCases unique per recipe", () => {
    for (const r of RECIPE_PRESETS) {
      expect(new Set(r.useCases).size).toBe(r.useCases.length);
    }
  });
  it("RecipeSchema validates showcase metadata", () => {
    const r = RECIPE_PRESETS[0];
    const parsed = RecipeSchema.safeParse(r);
    expect(parsed.success).toBe(true);
  });
});
