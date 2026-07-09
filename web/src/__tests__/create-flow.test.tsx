import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CreatePage } from "@/components/create-flow/create-page";

describe("CreatePage", () => {
  it("renders header and prompt input", () => {
    render(<CreatePage />);
    expect(screen.getByText("Create video")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Describe video you want to create...")).toBeInTheDocument();
  });
  it("renders grill button", () => {
    render(<CreatePage />);
    expect(screen.getByText("Grill prompt")).toBeInTheDocument();
  });
  it("renders options panel", () => {
    render(<CreatePage />);
    expect(screen.getByText("Options")).toBeInTheDocument();
  });
  it("renders progress sidebar", () => {
    render(<CreatePage />);
    expect(screen.getByText("Progress")).toBeInTheDocument();
    expect(screen.getByText("Grill prompt")).toBeInTheDocument();
  });
  it("shows grill panel placeholder", () => {
    render(<CreatePage />);
    expect(screen.getByText("Submit a prompt to see grill results")).toBeInTheDocument();
  });
});
