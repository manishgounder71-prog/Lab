import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCommandCenter, CommandCenterProvider } from "@/context/CommandCenterContext";
import type { ReactNode } from "react";

function wrapper({ children }: { children: ReactNode }) {
  return <CommandCenterProvider>{children}</CommandCenterProvider>;
}

describe("CommandCenterContext", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("should provide initial state with OPTIMAL severity", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });
    expect(result.current.state.severity).toBe("OPTIMAL");
    expect(result.current.state.scenarioState).toBe("INITIAL");
    expect(result.current.state.riskScore).toBe(0);
    expect(result.current.state.revenueAtRisk).toBe("$0");
    expect(result.current.state.simulationRunning).toBe(false);
  });

  it("should have all 10 initial agents with correct IDs", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });
    const agentIds = result.current.state.agents.map((a) => a.id);
    expect(agentIds).toContain("detection");
    expect(agentIds).toContain("sec");
    expect(agentIds).toContain("infra");
    expect(agentIds).toContain("legal");
    expect(agentIds).toContain("finance");
    expect(agentIds).toContain("cx");
    expect(agentIds).toContain("pr");
    expect(agentIds).toContain("ciso");
    expect(agentIds).toContain("cfo");
    expect(agentIds).toContain("ceo");
    expect(result.current.state.agents).toHaveLength(10);
  });

  it("should have 4 regional statuses all OPTIMAL initially", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });
    expect(result.current.state.regionalStatus).toHaveLength(4);
    result.current.state.regionalStatus.forEach((r) => {
      expect(r.status).toBe("OPTIMAL");
    });
  });

  it("should have correct decision matrix with 4 vectors", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });
    expect(result.current.state.decisionMatrix).toHaveLength(4);
    expect(result.current.state.decisionMatrix[0].vector).toBe("Security Risk");
    expect(result.current.state.decisionMatrix[1].vector).toBe("Revenue Impact");
    expect(result.current.state.decisionMatrix[2].vector).toBe("Recovery Time");
    expect(result.current.state.decisionMatrix[3].vector).toBe("Compliance Rating");
  });

  it("should have empty timeline, debate, and auditLogs initially", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });
    expect(result.current.state.timeline).toEqual([]);
    expect(result.current.state.debate).toEqual([]);
    expect(result.current.state.auditLogs).toEqual([]);
    expect(result.current.state.postMortem).toBeNull();
  });

  it("should start simulation and update state on startDemo when offline", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });

    // Should now be running with INC-001 scenario
    expect(result.current.state.simulationRunning).toBe(true);
    expect(result.current.state.scenarioId).toBe("INC-001");
    expect(result.current.state.scenarioTitle).toBe("Customer Database Breach");
  });

  it("should start the local simulation steps on startScenario", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startScenario("INC-003");
    });

    expect(result.current.state.simulationRunning).toBe(true);
    expect(result.current.state.scenarioId).toBe("INC-003");
    expect(result.current.state.scenarioTitle).toBe("Enterprise Ransomware Incident");
    // Should have the appropriate agents for this scenario
    const agentIds = result.current.state.agents.map((a) => a.id);
    expect(agentIds).toContain("sec");
    expect(agentIds).toContain("legal");
  });

  it("should update timeline and risk score after simulation steps", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });

    // Initially no timeline events before step runs
    expect(result.current.state.timeline).toHaveLength(0);

    // Advance past the first step (1000ms delay)
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // After first step, should have DETECTION state and 1 timeline event
    expect(result.current.state.scenarioState).toBe("DETECTION");
    expect(result.current.state.riskScore).toBe(70);
    expect(result.current.state.revenueAtRisk).toBe("$1.2M");
    expect(result.current.state.timeline).toHaveLength(1);
    expect(result.current.state.timeline[0].title).toBe("BREACH DETECTED");
    expect(result.current.state.auditLogs).toHaveLength(1);
  });

  it("should progress through investigation and legal phases", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });

    // Step 1: Detection (1000ms)
    act(() => { vi.advanceTimersByTime(1000); });
    expect(result.current.state.scenarioState).toBe("DETECTION");

    // Step 2: Investigation (4000ms from start = 3000ms more)
    act(() => { vi.advanceTimersByTime(3000); });
    expect(result.current.state.scenarioState).toBe("INVESTIGATION");
    expect(result.current.state.riskScore).toBe(85);
    expect(result.current.state.timeline).toHaveLength(2);

    // Step 3: Risk Legal (7000ms from start = 3000ms more)
    act(() => { vi.advanceTimersByTime(3000); });
    expect(result.current.state.scenarioState).toBe("RISK_LEGAL");
    expect(result.current.state.riskScore).toBe(94);
    expect(result.current.state.revenueAtRisk).toBe("$4.2M");
  });

  it("should reach DEBATE_ACTIVE phase and populate debate messages", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });

    // Advance through all steps to DEBATE_ACTIVE (1000 + 3000 + 3000 + 3000 = 10000ms)
    act(() => { vi.advanceTimersByTime(10000); });

    expect(result.current.state.scenarioState).toBe("DEBATE_ACTIVE");
    expect(result.current.state.debate.length).toBeGreaterThan(0);
    expect(result.current.state.debate[0].sender).toBe("CISO_SHIELD");
    expect(result.current.state.debate[0].sentiment).toBe("critical");
  });

  it("should resolve scenario with SHUTDOWN and generate post-mortem", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });

    // Advance to debate phase
    act(() => { vi.advanceTimersByTime(10000); });
    expect(result.current.state.scenarioState).toBe("DEBATE_ACTIVE");

    // Execute shutdown
    act(() => {
      result.current.deployCountermeasures("SHUTDOWN");
    });

    expect(result.current.state.scenarioState).toBe("RESOLVED");
    expect(result.current.state.severity).toBe("OPTIMAL");
    expect(result.current.state.riskScore).toBe(12);
    expect(result.current.state.simulationRunning).toBe(false);
    expect(result.current.state.postMortem).not.toBeNull();
    expect(result.current.state.postMortem?.rootCause).toContain("SQL Injection");
    // All agents should be SLEEPING after resolution
    result.current.state.agents.forEach((a) => {
      expect(a.status).toBe("SLEEPING");
    });
  });

  it("should resolve scenario with ISOLATION and higher risk score", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startScenario("INC-001");
    });
    act(() => { vi.advanceTimersByTime(10000); });

    act(() => {
      result.current.deployCountermeasures("ISOLATION");
    });

    expect(result.current.state.scenarioState).toBe("RESOLVED");
    expect(result.current.state.riskScore).toBe(45);
    expect(result.current.state.revenueAtRisk).toBe("$1.2M");
    expect(result.current.state.postMortem).not.toBeNull();
  });

  it("should reset state to initial values on resetDemo", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startDemo();
    });
    expect(result.current.state.simulationRunning).toBe(true);

    act(() => {
      result.current.resetDemo();
    });

    expect(result.current.state.scenarioState).toBe("INITIAL");
    expect(result.current.state.severity).toBe("OPTIMAL");
    expect(result.current.state.simulationRunning).toBe(false);
    expect(result.current.state.timeline).toEqual([]);
    expect(result.current.state.debate).toEqual([]);
    expect(result.current.state.postMortem).toBeNull();
  });

  it("should handle different scenario IDs correctly", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.startScenario("INC-010");
    });

    expect(result.current.state.scenarioTitle).toBe("Enterprise Perfect Storm");
    expect(result.current.state.shutdownLabel).toBe("EMERGENCY LOCKDOWN");
    expect(result.current.state.isolationLabel).toBe("SEGMENT CONTAINMENT");

    // Advance to debate
    act(() => { vi.advanceTimersByTime(10000); });
    expect(result.current.state.debate.length).toBeGreaterThan(0);
    // INC-010 has 4 debate messages
    expect(result.current.state.debate.length).toBe(4);
  });

  it("should set activeTab correctly", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    act(() => {
      result.current.setActiveTab("dashboard");
    });
    expect(result.current.activeTab).toBe("dashboard");

    act(() => {
      result.current.setActiveTab("war_room");
    });
    expect(result.current.activeTab).toBe("war_room");
  });

  it("should not update state when simulation is not running", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    // Try advancing timers without starting simulation
    act(() => { vi.advanceTimersByTime(10000); });

    // State should remain unchanged
    expect(result.current.state.scenarioState).toBe("INITIAL");
    expect(result.current.state.timeline).toEqual([]);
  });

  it("should track decision matrix values", () => {
    const { result } = renderHook(() => useCommandCenter(), { wrapper });

    const decisionMatrix = result.current.state.decisionMatrix;
    expect(decisionMatrix[0]).toEqual({ vector: "Security Risk", shutdownScore: 100, isolateScore: 28 });
    expect(decisionMatrix[1]).toEqual({ vector: "Revenue Impact", shutdownScore: 10, isolateScore: 85 });
    expect(decisionMatrix[2]).toEqual({ vector: "Recovery Time", shutdownScore: 30, isolateScore: 90 });
    expect(decisionMatrix[3]).toEqual({ vector: "Compliance Rating", shutdownScore: 95, isolateScore: 40 });
  });
});
