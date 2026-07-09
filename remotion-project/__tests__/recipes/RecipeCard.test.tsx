/**
 * RecipeCard component tests.
 */

import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { RecipeCard } from "../../src/recipes/RecipeCard";
import type { Recipe } from "../../src/recipes/types";

afterEach(cleanup);

const mockRecipe: Recipe = {
  id: "test-recipe",
  name: "Test Recipe",
  description: "A recipe for testing",
  previewText: "Preview text for test card",
  engines: ["remotion", "manim"],
  sceneKinds: ["title", "chart", "code"],
  useCases: ["Testing UI", "Demo purposes", "Example"],
  sortWeight: 50,
};

function rendered() {
  return render(<RecipeCard recipe={mockRecipe} />);
}

describe("RecipeCard", () => {
  it("renders recipe name", () => {
    rendered();
    expect(screen.getByText("Test Recipe")).toBeDefined();
  });

  it("renders description", () => {
    rendered();
    expect(screen.getByText("A recipe for testing")).toBeDefined();
  });

  it("renders preview text in default variant", () => {
    rendered();
    expect(screen.getByText("Preview text for test card")).toBeDefined();
  });

  it("renders engine badges", () => {
    rendered();
    // Use getAllByText + length to handle multiple renders from other tests
    expect(screen.getAllByText("remotion").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("manim").length).toBeGreaterThanOrEqual(1);
  });

  it("renders scene kind badges", () => {
    rendered();
    expect(screen.getAllByText("title").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("chart").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("code").length).toBeGreaterThanOrEqual(1);
  });

  it("renders use case badges in default variant", () => {
    rendered();
    expect(screen.getAllByText("Testing UI").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Demo purposes").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Example").length).toBeGreaterThanOrEqual(1);
  });

  it("renders Select button", () => {
    rendered();
    expect(screen.getAllByText("Select").length).toBeGreaterThanOrEqual(1);
  });

  it("renders Selected when selected", () => {
    render(<RecipeCard recipe={mockRecipe} selected />);
    expect(screen.getByText("Selected")).toBeDefined();
  });

  it("calls onSelect when button clicked", () => {
    const onSelect = vi.fn();
    render(<RecipeCard recipe={mockRecipe} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Select"));
    expect(onSelect).toHaveBeenCalledWith(mockRecipe);
  });

  it("calls onSelect when card key pressed", () => {
    const onSelect = vi.fn();
    render(<RecipeCard recipe={mockRecipe} onSelect={onSelect} />);
    // First role="button" is the card itself (before the <button> child)
    const cards = screen.getAllByRole("button");
    const cardDiv = cards.find((el) => el.tagName === "DIV");
    expect(cardDiv).toBeDefined();
    fireEvent.keyDown(cardDiv!, { key: "Enter" });
    expect(onSelect).toHaveBeenCalledWith(mockRecipe);
  });

  it("compact variant hides preview text", () => {
    render(<RecipeCard recipe={mockRecipe} variant="compact" />);
    expect(screen.queryByText("Preview text for test card")).toBeNull();
  });

  it("does not render use cases in compact variant", () => {
    render(<RecipeCard recipe={mockRecipe} variant="compact" />);
    expect(screen.queryByText("Testing UI")).toBeNull();
  });
});
