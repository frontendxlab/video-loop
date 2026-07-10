import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TemplatePicker } from "@/components/create-flow/template-picker";
import { GENRE_TEMPLATES } from "@/contracts/create";

describe("TemplatePicker", () => {
  const onSelect = vi.fn();

  beforeEach(() => {
    onSelect.mockClear();
  });

  it("renders header", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    expect(screen.getByText("Templates")).toBeInTheDocument();
  });

  it("renders all genre templates", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    for (const t of GENRE_TEMPLATES) {
      expect(screen.getByText(t.name)).toBeInTheDocument();
    }
  });

  it("shows category badges", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    for (const t of GENRE_TEMPLATES) {
      expect(screen.getAllByText(t.category).length).toBeGreaterThan(0);
    }
  });

  it("shows scene preview chips", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    const first = GENRE_TEMPLATES[0];
    // Use getAllByText since many templates share "1. title"
    const chips = screen.getAllByText(`${1}. ${first.scenes[0].sceneType}`);
    expect(chips.length).toBeGreaterThanOrEqual(1);
    // Each template renders its scene count
    const scenesChips = screen.getAllByText(/^(\d+)\.\s\w+$/);
    expect(scenesChips.length).toBeGreaterThanOrEqual(first.scenes.length);
  });

  it("calls onSelect with template id on click", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    fireEvent.click(screen.getByText("Explainer"));
    expect(onSelect).toHaveBeenCalledWith(["explainer"]);
  });

  it("deselects when clicked again", () => {
    render(<TemplatePicker selected={["explainer"]} onSelect={onSelect} suggestions={[]} />);
    fireEvent.click(screen.getByText("Explainer"));
    expect(onSelect).toHaveBeenCalledWith([]);
  });

  it("allows multiple selection", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    fireEvent.click(screen.getByText("Explainer"));
    fireEvent.click(screen.getByText("Tutorial"));
    expect(onSelect).toHaveBeenLastCalledWith(["tutorial"]);
  });

  it("shows selected count when templates selected", () => {
    render(<TemplatePicker selected={["explainer", "tutorial"]} onSelect={onSelect} suggestions={[]} />);
    expect(screen.getByText("2 selected")).toBeInTheDocument();
  });

  it("does not toggle when disabled", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} disabled />);
    fireEvent.click(screen.getByText("Explainer"));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("renders all genre templates as buttons", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    // Each template card is a button
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(GENRE_TEMPLATES.length);
  });

  it("shows description for each template", () => {
    render(<TemplatePicker selected={[]} onSelect={onSelect} suggestions={[]} />);
    for (const t of GENRE_TEMPLATES) {
      expect(screen.getByText(t.description)).toBeInTheDocument();
    }
  });
});
