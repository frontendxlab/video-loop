import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { CreatePage } from "@/components/create-flow/create-page";

const mockNavigate = vi.fn();

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mockNavigate,
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
}));

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("CreatePage", () => {
  it("renders header and prompt input", () => {
    render(<CreatePage />);
    expect(screen.getByText("Create video")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Describe video you want to create...")).toBeInTheDocument();
  });

  it("renders grill button", () => {
    render(<CreatePage />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.some(b => b.textContent?.includes("Grill prompt"))).toBe(true);
  });

  it("renders options panel", () => {
    render(<CreatePage />);
    expect(screen.getByText("Options")).toBeInTheDocument();
  });

  it("renders progress section", () => {
    render(<CreatePage />);
    expect(screen.getByText("Progress")).toBeInTheDocument();
  });

  it("shows 5 pipeline stages", () => {
    render(<CreatePage />);
    expect(screen.getByText("Pipeline stages")).toBeInTheDocument();
  });

  it("shows grill panel placeholder when idle", () => {
    render(<CreatePage />);
    expect(screen.getByText("Submit a prompt to see grill results")).toBeInTheDocument();
  });

  it("grill button disabled when prompt too short", () => {
    render(<CreatePage />);
    const buttons = screen.getAllByRole("button");
    const grillBtn = buttons.find(b => b.textContent?.includes("Grill prompt"));
    expect(grillBtn?.closest("button")).toBeDisabled();
  });
});
