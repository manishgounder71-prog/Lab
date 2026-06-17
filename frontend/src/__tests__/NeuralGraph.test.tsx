import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { CommandCenterProvider } from "@/context/CommandCenterContext";
import NeuralGraph from "@/components/NeuralGraph";
import type { ReactNode } from "react";

function wrapper({ children }: { children: ReactNode }) {
  return <CommandCenterProvider>{children}</CommandCenterProvider>;
}

describe("NeuralGraph", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("should render the workflow orchestrator header", () => {
    render(<NeuralGraph />, { wrapper });
    expect(screen.getByText("MULTI-AGENT WORKFLOW ORCHESTRATOR")).toBeInTheDocument();
  });

  it("should show ACTIVE LINKS count", () => {
    render(<NeuralGraph />, { wrapper });
    // There are 12 connections defined in CONNECTIONS
    expect(screen.getByText(/ACTIVE LINKS: 12/)).toBeInTheDocument();
  });

  it("should render 5 stage headers", () => {
    render(<NeuralGraph />, { wrapper });
    expect(screen.getByText("01 | INGESTION")).toBeInTheDocument();
    expect(screen.getByText("02 | TRIAGE")).toBeInTheDocument();
    expect(screen.getByText("03 | ANALYSIS")).toBeInTheDocument();
    expect(screen.getByText("04 | ADVISORY")).toBeInTheDocument();
    expect(screen.getByText("05 | BOARD ROOM")).toBeInTheDocument();
  });

  it("should render control buttons", () => {
    render(<NeuralGraph />, { wrapper });
    expect(screen.getByTitle("Toggle Grid")).toBeInTheDocument();
    expect(screen.getByTitle("Reset View & Pan")).toBeInTheDocument();
    expect(screen.getByTitle("Zoom In")).toBeInTheDocument();
    expect(screen.getByTitle("Zoom Out")).toBeInTheDocument();
  });

  it("should render TRIGGER FLOW button when simulation not running", () => {
    render(<NeuralGraph />, { wrapper });
    expect(screen.getByText("TRIGGER FLOW")).toBeInTheDocument();
  });

  it("should show the zoom percentage", () => {
    render(<NeuralGraph />, { wrapper });
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("should render the canvas footer text", () => {
    render(<NeuralGraph />, { wrapper });
    expect(
      screen.getByText(/DRAG CANVAS TO PAN/)
    ).toBeInTheDocument();
  });

  it("should apply SVG stage divider lines", () => {
    const { container } = render(<NeuralGraph />, { wrapper });
    // Should have SVG element
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("should have correct grid class toggle based on default state", () => {
    const { container } = render(<NeuralGraph />, { wrapper });
    // The dot-grid is applied when showGrid is true
    const gridArea = container.querySelector(".dot-grid");
    expect(gridArea).toBeInTheDocument();
  });
});
