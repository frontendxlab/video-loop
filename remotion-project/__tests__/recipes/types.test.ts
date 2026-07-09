/**
 * Recipe types/schema tests.
 */

import { describe, it, expect } from "vitest";
import {
  RecipeSchema,
  EngineSchema,
  SceneKindSchema,
  validateRecipe,
  validateRecipeRegistry,
  toDisplayMeta,
} from "../../src/recipes/types";

describe("EngineSchema", () => {
  it("accepts valid engines", () => {
    expect(EngineSchema.parse("remotion")).toBe("remotion");
    expect(EngineSchema.parse("manim")).toBe("manim");
    expect(EngineSchema.parse("animotion")).toBe("animotion");
  });

  it("rejects invalid engine", () => {
    expect(() => EngineSchema.parse("blender")).toThrow();
  });
});

describe("SceneKindSchema", () => {
  it("accepts built-in scene kinds", () => {
    expect(SceneKindSchema.parse("title")).toBe("title");
    expect(SceneKindSchema.parse("code")).toBe("code");
    expect(SceneKindSchema.parse("chart")).toBe("chart");
  });

  it("accepts showcase scene kinds", () => {
    expect(SceneKindSchema.parse("map3d")).toBe("map3d");
    expect(SceneKindSchema.parse("audio-reactive")).toBe("audio-reactive");
    expect(SceneKindSchema.parse("3d-ranking")).toBe("3d-ranking");
  });

  it("rejects unknown scene kind", () => {
    expect(() => SceneKindSchema.parse("unknown-kind")).toThrow();
  });
});

describe("RecipeSchema", () => {
  const validRecipe = {
    id: "test-recipe",
    name: "Test Recipe",
    description: "A test recipe",
    previewText: "Preview of test recipe",
    engines: ["remotion"],
    sceneKinds: ["title"],
    useCases: ["Testing"],
    sortWeight: 50,
  };

  it("accepts minimal valid recipe", () => {
    const r = RecipeSchema.parse(validRecipe);
    expect(r.id).toBe("test-recipe");
    expect(r.sortWeight).toBe(50);
  });

  it("defaults sortWeight to 0 when omitted", () => {
    const { sortWeight, ...without } = validRecipe;
    const r = RecipeSchema.parse(without);
    expect(r.sortWeight).toBe(0);
  });

  it("accepts full recipe with all opt fields", () => {
    const full = {
      ...validRecipe,
      inputs: { prompt: "make a video" },
      transitionPack: "smooth",
      reviewRules: ["check-readability"],
    };
    expect(() => RecipeSchema.parse(full)).not.toThrow();
  });

  it("rejects recipe without engines", () => {
    expect(() =>
      RecipeSchema.parse({ ...validRecipe, engines: [] }),
    ).toThrow();
  });

  it("rejects recipe empty name", () => {
    expect(() =>
      RecipeSchema.parse({ ...validRecipe, name: "" }),
    ).toThrow();
  });
});

describe("validateRecipe", () => {
  it("returns parsed recipe on valid input", () => {
    const r = validateRecipe({
      id: "v",
      name: "V",
      description: "D",
      previewText: "P",
      engines: ["manim"],
      sceneKinds: ["chart"],
      useCases: ["U"],
    });
    expect(r.id).toBe("v");
  });

  it("throws on invalid", () => {
    expect(() => validateRecipe({})).toThrow();
  });
});

describe("validateRecipeRegistry", () => {
  it("validates array of recipes", () => {
    const result = validateRecipeRegistry([
      { id: "a", name: "A", description: "D", previewText: "P", engines: ["remotion"], sceneKinds: ["title"], useCases: ["U"] },
      { id: "b", name: "B", description: "D", previewText: "P", engines: ["manim"], sceneKinds: ["chart"], useCases: ["U"] },
    ]);
    expect(result).toHaveLength(2);
  });
});

describe("toDisplayMeta", () => {
  it("extracts display fields", () => {
    const r = {
      id: "x", name: "X", description: "D", previewText: "P",
      engines: ["remotion"], sceneKinds: ["title"], useCases: ["U"],
      sortWeight: 10,
    };
    const m = toDisplayMeta(r);
    expect(m.id).toBe("x");
    expect(m.engines).toEqual(["remotion"]);
    expect("inputs" in m).toBe(false);
  });
});
