/**
 * Recipe registry integrity tests.
 */

import { describe, it, expect } from "vitest";
import {
  recipeRegistry,
  getSortedRecipes,
  getRecipeById,
  getRecipesByEngine,
  getRecipesBySceneKind,
  getAllEngines,
  getAllSceneKinds,
  getAllUseCases,
} from "../../src/recipes/registry";
import { validateRecipeRegistry } from "../../src/recipes/types";

describe("recipeRegistry", () => {
  it("is not empty", () => {
    expect(recipeRegistry.length).toBeGreaterThan(0);
  });

  it("all recipes pass schema validation", () => {
    expect(() => validateRecipeRegistry(recipeRegistry)).not.toThrow();
  });

  it("all ids are unique", () => {
    const ids = recipeRegistry.map((r) => r.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("every id is kebab-case", () => {
    for (const r of recipeRegistry) {
      expect(r.id).toMatch(/^[a-z0-9][a-z0-9-]*$/);
    }
  });

  it("every recipe has at least 1 engine", () => {
    for (const r of recipeRegistry) {
      expect(r.engines.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("every recipe has at least 1 scene kind", () => {
    for (const r of recipeRegistry) {
      expect(r.sceneKinds.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("every recipe has at least 1 use case", () => {
    for (const r of recipeRegistry) {
      expect(r.useCases.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("all recipes have non-empty, non-blank fields", () => {
    for (const r of recipeRegistry) {
      expect(r.name.trim()).toBeTruthy();
      expect(r.description.trim()).toBeTruthy();
      expect(r.previewText.trim()).toBeTruthy();
    }
  });

  it("sortWeight is a non-negative integer when set", () => {
    for (const r of recipeRegistry) {
      if (r.sortWeight !== undefined) {
        expect(Number.isInteger(r.sortWeight)).toBe(true);
        expect(r.sortWeight).toBeGreaterThanOrEqual(0);
      }
    }
  });
});

describe("getSortedRecipes", () => {
  it("returns recipes sorted by weight descending", () => {
    const sorted = getSortedRecipes();
    for (let i = 1; i < sorted.length; i++) {
      expect((sorted[i - 1].sortWeight ?? 0)).toBeGreaterThanOrEqual(sorted[i].sortWeight ?? 0);
    }
  });
});

describe("getRecipeById", () => {
  it("finds existing recipe", () => {
    const r = getRecipeById("travel-route-3d");
    expect(r).toBeDefined();
    expect(r!.name).toContain("Travel");
  });

  it("returns undefined for missing", () => {
    expect(getRecipeById("nonexistent")).toBeUndefined();
  });
});

describe("getRecipesByEngine", () => {
  it("returns recipes for remotion", () => {
    const results = getRecipesByEngine("remotion");
    expect(results.length).toBeGreaterThan(0);
    results.forEach((r) => expect(r.engines).toContain("remotion"));
  });

  it("returns recipes for manim", () => {
    const results = getRecipesByEngine("manim");
    expect(results.length).toBeGreaterThan(0);
    results.forEach((r) => expect(r.engines).toContain("manim"));
  });

  it("returns recipes for animotion", () => {
    const results = getRecipesByEngine("animotion");
    expect(results.length).toBeGreaterThan(0);
    results.forEach((r) => expect(r.engines).toContain("animotion"));
  });
});

describe("getRecipesBySceneKind", () => {
  it("filters by scene kind", () => {
    const results = getRecipesBySceneKind("chart");
    expect(results.length).toBeGreaterThan(0);
    results.forEach((r) => expect(r.sceneKinds).toContain("chart"));
  });
});

describe("getAllEngines", () => {
  it("returns all engine types", () => {
    const engines = getAllEngines();
    expect(engines).toContain("remotion");
    expect(engines).toContain("manim");
    expect(engines).toContain("animotion");
  });
});

describe("getAllSceneKinds", () => {
  it("returns scene kinds present in registry", () => {
    const kinds = getAllSceneKinds();
    expect(kinds.length).toBeGreaterThan(0);
    expect(kinds).toContain("title");
    expect(kinds).toContain("chart");
  });
});

describe("getAllUseCases", () => {
  it("returns use cases present in registry", () => {
    const cases = getAllUseCases();
    expect(cases.length).toBeGreaterThan(0);
  });
});
