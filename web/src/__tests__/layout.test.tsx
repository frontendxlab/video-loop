import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Topbar } from "@/components/topbar";

describe("Topbar", () => {
  it("renders app name", () => {
    render(<Topbar />);
    expect(screen.getByText("VideoForge")).toBeInTheDocument();
  });

  it("shows idle status", () => {
    render(<Topbar />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });
});
