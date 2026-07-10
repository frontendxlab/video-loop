import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RecipePicker } from "@/components/create-flow/recipe-picker";
import { RECIPE_PRESETS } from "@/contracts/create";

describe("RecipePicker", () => {
  const onSelect = vi.fn();

  it("renders collapsed by default", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    expect(screen.getByText("Recipe")).toBeInTheDocument();
    expect(screen.getByText(/Pick a recipe to guide scene structure/)).toBeInTheDocument();
  });

  it("shows recipes when clicked", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.getByText("Hero intro")).toBeInTheDocument();
    expect(screen.getByText("No recipe")).toBeInTheDocument();
  });

  it("shows all preset recipes", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    for (const recipe of RECIPE_PRESETS) {
      expect(screen.getByText(recipe.name)).toBeInTheDocument();
    }
  });

  it("calls onSelect when recipe clicked", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    fireEvent.click(screen.getByText("Hero intro"));
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: "hero-intro", name: "Hero intro" }),
    );
  });

  it("deselects when same recipe clicked again", () => {
    const recipe = RECIPE_PRESETS[0];
    render(<RecipePicker selected={recipe} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    const buttons = screen.getAllByText("Hero intro");
    fireEvent.click(buttons[buttons.length - 1]);
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("calls onSelect with null when 'No recipe' clicked", () => {
    render(<RecipePicker selected={RECIPE_PRESETS[0]} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    fireEvent.click(screen.getByText("No recipe"));
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("shows selected recipe name as badge", () => {
    render(<RecipePicker selected={RECIPE_PRESETS[1]} onSelect={onSelect} />);
    expect(screen.getByText("Document highlight")).toBeInTheDocument();
  });

  it("shows engine badge on recipe items", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.getAllByText("remotion").length).toBeGreaterThan(0);
    expect(screen.getAllByText("manim").length).toBeGreaterThan(0);
  });

  it("does not toggle when disabled", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} disabled />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.queryByText("Hero intro")).not.toBeInTheDocument();
  });

  it("shows engine badges with labels on recipe items", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    // Engine names appear as badges
    expect(screen.getAllByText("remotion").length).toBeGreaterThan(0);
  });

  it("shows use cases on recipe items", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    // First recipe use case should be visible
    const first = RECIPE_PRESETS[0];
    expect(screen.getByText(first.useCases[0])).toBeInTheDocument();
  });

  it("shows motion hints when recipe is selected", () => {
    const recipe = RECIPE_PRESETS[0];
    render(<RecipePicker selected={recipe} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.getByText(`In: ${recipe.motionHints.entrance}`)).toBeInTheDocument();
    expect(screen.getByText(`Out: ${recipe.motionHints.exit}`)).toBeInTheDocument();
  });

  it("shows review hints when recipe is selected", () => {
    const recipe = RECIPE_PRESETS[0];
    render(<RecipePicker selected={recipe} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    for (const hint of recipe.reviewHints) {
      expect(screen.getByText(hint)).toBeInTheDocument();
    }
  });

  it("does not show motion hints when no recipe selected", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.queryByText("In:")).not.toBeInTheDocument();
  });

  it("does not show review hints when no recipe selected", () => {
    render(<RecipePicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Recipe"));
    expect(screen.queryByText("⚠")).not.toBeInTheDocument();
  });
});
