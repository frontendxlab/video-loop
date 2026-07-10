import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RecipeShowcase } from "@/components/recipes/recipe-showcase";
import { RECIPE_PRESETS } from "@/contracts/create";

describe("RecipeShowcase", () => {
  it("renders page title with recipe count", () => {
    render(<RecipeShowcase />);
    expect(screen.getByText("Recipes")).toBeInTheDocument();
    expect(screen.getByText(`${RECIPE_PRESETS.length} showcase patterns`, { exact: false })).toBeInTheDocument();
  });

  it("renders all recipe cards", () => {
    render(<RecipeShowcase />);
    for (const recipe of RECIPE_PRESETS) {
      expect(screen.getByText(recipe.name)).toBeInTheDocument();
    }
  });

  it("shows engine badges per recipe", () => {
    render(<RecipeShowcase />);
    // remotion and manim appear across recipes
    const remotionBadges = screen.getAllByText("remotion");
    expect(remotionBadges.length).toBeGreaterThanOrEqual(
      RECIPE_PRESETS.filter((r) => r.preferredEngine === "remotion").length,
    );
  });

  it("shows use cases as chips", () => {
    render(<RecipeShowcase />);
    const first = RECIPE_PRESETS[0];
    for (const uc of first.useCases) {
      expect(screen.getByText(uc)).toBeInTheDocument();
    }
  });

  it("shows motion hints for each recipe", () => {
    render(<RecipeShowcase />);
    for (const recipe of RECIPE_PRESETS) {
      // Use substring match; each motion hint text is unique per recipe
      const entranceEl = screen.getByText(recipe.motionHints.entrance);
      expect(entranceEl).toBeInTheDocument();
      const exitEl = screen.getByText(recipe.motionHints.exit);
      expect(exitEl).toBeInTheDocument();
    }
  });

  it("shows review hints for each recipe", () => {
    render(<RecipeShowcase />);
    // Use getAllByText since some hints may be partial matches of others
    for (const recipe of RECIPE_PRESETS) {
      for (const hint of recipe.reviewHints) {
        const matches = screen.getAllByText(hint);
        expect(matches.length).toBeGreaterThanOrEqual(1);
      }
    }
  });

  it("shows inputs per recipe", () => {
    render(<RecipeShowcase />);
    for (const recipe of RECIPE_PRESETS) {
      for (const inp of recipe.allowedInputs) {
        const keyEls = screen.getAllByText(inp.key);
        expect(keyEls.length).toBeGreaterThanOrEqual(1);
      }
    }
  });

  it("shows tags per recipe", () => {
    render(<RecipeShowcase />);
    // Tags can repeat across recipes (e.g. "fade_out", "data")
    const firstRecipeTags = RECIPE_PRESETS[0].tags;
    for (const tag of firstRecipeTags) {
      const matches = screen.getAllByText(tag);
      expect(matches.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("renders info footer", () => {
    render(<RecipeShowcase />);
    expect(screen.getByText(/Engine badges show/)).toBeInTheDocument();
  });
});
