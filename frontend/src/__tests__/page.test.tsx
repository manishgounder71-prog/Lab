import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@/test/test-utils";
import Page from "@/app/page";

// Mock recharts to avoid SVG rendering issues
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
}));

// Mock the Three.js SeverityOrb component (it's dynamic imported)
vi.mock("@/components/SeverityOrb", () => ({
  default: () => <div data-testid="severity-orb" />,
}));

// Mock SpaceBackground to avoid canvas issues
vi.mock("@/components/SpaceBackground", () => ({
  default: () => <div data-testid="space-background" />,
}));

describe("Page Component", () => {
  it("should render the hero section", () => {
    const { container } = render(<Page />);
    // Find all h1 elements and check the one with the hero text
    const headings = container.querySelectorAll("h1");
    const heroHeading = Array.from(headings).find(h => 
      h.textContent?.includes("Enterprise Crisis Command Center")
    );
    expect(heroHeading).toBeTruthy();
    expect(screen.getByText(/Multi-agent collaborative war room/)).toBeInTheDocument();
  });

  it("should render SYSTEM STATUS indicator", () => {
    render(<Page />);
    // SYSTEM STATUS appears multiple times; verify at least one exists
    const indicators = screen.getAllByText(/SYSTEM STATUS:/);
    expect(indicators.length).toBeGreaterThanOrEqual(1);
  });

  it("should render all navigation buttons in the header", () => {
    render(<Page />);
    expect(screen.getByText("CONSOLE HOME")).toBeInTheDocument();
    expect(screen.getByText("LIVE TELEMETRY")).toBeInTheDocument();
    expect(screen.getByText("SDK ORCHESTRATOR")).toBeInTheDocument();
    expect(screen.getByText("COMMAND DECISIONS")).toBeInTheDocument();
    expect(screen.getByText("SIMULATION DECK")).toBeInTheDocument();
  });

  it("should render the SIMULATE BREACH DEMO button when not running", () => {
    render(<Page />);
    expect(screen.getByText("SIMULATE BREACH DEMO")).toBeInTheDocument();
  });

  it("should render action buttons in hero section", () => {
    render(<Page />);
    expect(screen.getByText("LAUNCH WAR ROOM")).toBeInTheDocument();
    expect(screen.getByText("EXECUTIVE SUMMARY")).toBeInTheDocument();
  });

  it("should render the simulation center section heading", () => {
    render(<Page />);
    expect(screen.getByText("Cyber Simulation")).toBeInTheDocument();
    expect(screen.getByText("Deck")).toBeInTheDocument();
  });

  it("should render all 10 scenario cards in simulation center", () => {
    render(<Page />);
    expect(screen.getByText("Customer Database Breach")).toBeInTheDocument();
    expect(screen.getByText("Regional Cloud Outage")).toBeInTheDocument();
    expect(screen.getByText("Enterprise Ransomware Incident")).toBeInTheDocument();
    expect(screen.getByText("GDPR Compliance Violation")).toBeInTheDocument();
    expect(screen.getByText("Brand Reputation Crisis")).toBeInTheDocument();
    expect(screen.getByText("Malicious Insider Activity")).toBeInTheDocument();
    expect(screen.getByText("Global Product Recall")).toBeInTheDocument();
    expect(screen.getByText("Large Scale Financial Fraud")).toBeInTheDocument();
    expect(screen.getByText("Global Supply Chain Failure")).toBeInTheDocument();
    expect(screen.getByText("Enterprise Perfect Storm")).toBeInTheDocument();
  });

  it("should render the dashboard section with initial values", () => {
    render(<Page />);
    expect(screen.getByText("Systems Operating Normally")).toBeInTheDocument();
    expect(screen.getByText("$0")).toBeInTheDocument(); // revenue at risk
    expect(screen.getByText("00")).toBeInTheDocument(); // nodes compromised padded
  });

  it("should render agent cards in the overview", () => {
    render(<Page />);
    // Agent names appear in both overview cards and the live telemetry section
    expect(screen.getAllByText("Cyber Threat Containment Agent").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Cloud Infrastructure & Failover Architect").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Data Protection & Legal Compliance Shield").length).toBeGreaterThanOrEqual(1);
  });

  it("should render the incident timeline section", () => {
    render(<Page />);
    expect(screen.getAllByText(/REAL-TIME INCIDENT TIMELINE/).length).toBeGreaterThanOrEqual(1);
  });

  it("should render the C-suite debate section", () => {
    render(<Page />);
    expect(screen.getByText("REAL-TIME C-SUITE DEBATE")).toBeInTheDocument();
  });

  it("should render the strategic decision matrix", () => {
    render(<Page />);
    expect(screen.getByText("STRATEGIC DECISION MATRIX")).toBeInTheDocument();
  });

  it("should render all severity badges on scenario cards", () => {
    render(<Page />);
    const severities = screen.getAllByText(/^(CRITICAL|HIGH|MEDIUM|MAXIMUM)$/);
    expect(severities.length).toBeGreaterThanOrEqual(10); // 10 scenarios
  });

  it("should have scroll margins on sections", () => {
    const { container } = render(<Page />);
    const sections = container.querySelectorAll("[id]");
    const sectionIds = Array.from(sections).map((s) => s.id);
    expect(sectionIds).toContain("overview");
    expect(sectionIds).toContain("dashboard");
    expect(sectionIds).toContain("war_room");
    expect(sectionIds).toContain("board_room");
    expect(sectionIds).toContain("simulation");
  });
});
