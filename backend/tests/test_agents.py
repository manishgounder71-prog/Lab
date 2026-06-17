"""Tests for agents module — data structures, scenario definitions, and utility functions."""

import pytest
from agents import (
    ALL_AGENTS,
    SCENARIOS,
    CrisisScenarioStep,
    ScenarioDefinition,
    get_resolution_step,
)


class TestAllAgents:
    """Verify the ALL_AGENTS registry has the correct structure."""

    def test_has_required_agents(self):
        """Must include all 16 core agents."""
        expected_ids = {
            "detection", "sec", "infra", "legal", "finance",
            "cx", "pr", "recovery", "risk", "hr", "ops",
            "marketing", "cto", "ceo", "cfo", "ciso",
        }
        actual_ids = {info["id"] for info in ALL_AGENTS.values()}
        assert actual_ids == expected_ids, f"Missing agents: {expected_ids - actual_ids}"

    def test_every_agent_has_required_fields(self):
        """Each agent entry must have id, name, role, status, lastMessage, tags."""
        required_keys = {"id", "name", "role", "status", "lastMessage", "tags"}
        for name, info in ALL_AGENTS.items():
            missing = required_keys - info.keys()
            assert not missing, f"Agent '{name}' missing fields: {missing}"

    def test_all_agents_start_idle(self):
        """All agents should start with IDLE status."""
        for name, info in ALL_AGENTS.items():
            assert info["status"] == "IDLE", f"Agent '{name}' not IDLE: {info['status']}"

    def test_tags_is_list_of_strings(self):
        """tags must be a non-empty list of strings."""
        for name, info in ALL_AGENTS.items():
            assert isinstance(info["tags"], list), f"Agent '{name}' tags not a list"
            assert len(info["tags"]) > 0, f"Agent '{name}' has empty tags"
            for tag in info["tags"]:
                assert isinstance(tag, str), f"Agent '{name}' has non-string tag: {tag}"

    def test_no_duplicate_agent_ids(self):
        """No two agents should share the same id."""
        ids = [info["id"] for info in ALL_AGENTS.values()]
        assert len(ids) == len(set(ids)), "Duplicate agent ids found"


class TestScenariosRegistry:
    """Verify all 10 scenarios are defined correctly."""

    def test_all_expected_scenarios_exist(self):
        """Must have exactly 10 scenarios INC-001 through INC-010."""
        expected_ids = {f"INC-{i:03d}" for i in range(1, 11)}
        assert set(SCENARIOS.keys()) == expected_ids
        assert len(SCENARIOS) == 10

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_scenario_is_valid_scenario_definition(self, sc_id):
        """Each scenario must be a ScenarioDefinition instance."""
        scenario = SCENARIOS[sc_id]
        assert isinstance(scenario, ScenarioDefinition)

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_required_fields(self, sc_id):
        """Each scenario must have required fields populated."""
        scenario = SCENARIOS[sc_id]
        assert scenario.id, f"{sc_id} missing id"
        assert scenario.title, f"{sc_id} missing title"
        assert scenario.severity, f"{sc_id} missing severity"
        assert scenario.description, f"{sc_id} missing description"
        assert scenario.estimated_impact, f"{sc_id} missing estimated_impact"
        assert len(scenario.agents_involved) > 0, f"{sc_id} no agents_involved"
        assert len(scenario.steps) > 0, f"{sc_id} no steps"
        assert len(scenario.resolutions) == 2, f"{sc_id} must have 2 resolutions"
        assert "SHUTDOWN" in scenario.resolutions, f"{sc_id} missing SHUTDOWN resolution"
        assert "ISOLATION" in scenario.resolutions, f"{sc_id} missing ISOLATION resolution"

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_agents_involved_are_valid(self, sc_id):
        """Every agent name in agents_involved must exist in ALL_AGENTS."""
        scenario = SCENARIOS[sc_id]
        for agent_name in scenario.agents_involved:
            assert agent_name in ALL_AGENTS, (
                f"{sc_id} references unknown agent '{agent_name}'"
            )

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_severity_is_valid(self, sc_id):
        """Severity must be one of the allowed values."""
        valid = {"Critical", "High", "Medium", "Maximum"}
        assert SCENARIOS[sc_id].severity in valid, (
            f"{sc_id} invalid severity: {SCENARIOS[sc_id].severity}"
        )

    def test_scenario_severity_distribution(self):
        """INC-010 should be the only 'Maximum' scenario."""
        maximum_scenarios = [
            sid for sid, s in SCENARIOS.items() if s.severity == "Maximum"
        ]
        assert maximum_scenarios == ["INC-010"]

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_shutdown_and_isolation_labels_differ(self, sc_id):
        """shutdown_label and isolation_label must be different."""
        s = SCENARIOS[sc_id]
        assert s.shutdown_label != s.isolation_label, (
            f"{sc_id} shutdown and isolation labels are identical"
        )


class TestScenarioSteps:
    """Verify each scenario's steps are valid CrisisScenarioStep instances."""

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_steps_have_progressive_risk(self, sc_id):
        """Risk scores should generally increase through the steps (non-decreasing)."""
        steps = SCENARIOS[sc_id].steps
        for i in range(1, len(steps)):
            assert steps[i].risk_score >= steps[i - 1].risk_score, (
                f"{sc_id} step {i} risk decreased: "
                f"{steps[i-1].risk_score} -> {steps[i].risk_score}"
            )

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_last_step_is_debate_active(self, sc_id):
        """The final step should always be DEBATE_ACTIVE."""
        last_step = SCENARIOS[sc_id].steps[-1]
        assert last_step.step_name == "DEBATE_ACTIVE", (
            f"{sc_id} final step is {last_step.step_name}, expected DEBATE_ACTIVE"
        )

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_debate_step_has_messages(self, sc_id):
        """The DEBATE_ACTIVE step must have at least 3 debate messages."""
        last_step = SCENARIOS[sc_id].steps[-1]
        assert len(last_step.debate_messages) >= 3, (
            f"{sc_id} DEBATE_ACTIVE has {len(last_step.debate_messages)} messages, expected >=3"
        )


class TestResolutions:
    """Verify resolution steps are valid."""

    def test_shutdown_lowers_risk_for_all_except_inc009(self):
        """For most scenarios, SHUTDOWN risk < ISOLATION risk.
        INC-009 (Supply Chain) is inverted — halting production is riskier
        than air-freighting alternative parts.
        """
        for sc_id in SCENARIOS:
            shutdown = SCENARIOS[sc_id].resolutions["SHUTDOWN"]
            isolation = SCENARIOS[sc_id].resolutions["ISOLATION"]
            if sc_id == "INC-009":
                # Supply chain: shutdown (halt production) is riskier than isolation (air freight)
                assert shutdown.risk_score > isolation.risk_score, (
                    f"{sc_id}: expected SHUTDOWN risk > ISOLATION risk, "
                    f"got {shutdown.risk_score} <= {isolation.risk_score}"
                )
            else:
                assert shutdown.risk_score < isolation.risk_score, (
                    f"{sc_id}: SHUTDOWN risk ({shutdown.risk_score}) >= "
                    f"ISOLATION risk ({isolation.risk_score})"
                )

    @pytest.mark.parametrize("sc_id", [f"INC-{i:03d}" for i in range(1, 11)])
    def test_resolution_step_name_is_resolved(self, sc_id):
        """Both resolution steps should have step_name 'RESOLVED'."""
        for decision in ("SHUTDOWN", "ISOLATION"):
            step = SCENARIOS[sc_id].resolutions[decision]
            assert step.step_name == "RESOLVED", (
                f"{sc_id} {decision} resolution has step_name '{step.step_name}'"
            )


class TestGetResolutionStep:
    """Test the get_resolution_step utility function."""

    def test_returns_shutdown_by_default(self):
        """Unknown decision should fall back to SHUTDOWN."""
        step = get_resolution_step("UNKNOWN_DECISION", "INC-001")
        assert step.risk_score == 12  # INC-001 SHUTDOWN risk score

    def test_returns_correct_shutdown(self):
        step = get_resolution_step("SHUTDOWN", "INC-001")
        assert step.step_name == "RESOLVED"
        assert step.risk_score == 12

    def test_returns_correct_isolation(self):
        step = get_resolution_step("ISOLATION", "INC-001")
        assert step.step_name == "RESOLVED"
        assert step.risk_score == 45

    def test_unknown_scenario_falls_back_to_inc001(self):
        """An unknown scenario id should default to INC-001."""
        step = get_resolution_step("SHUTDOWN", "UNKNOWN")
        assert step.risk_score == 12  # INC-001 SHUTDOWN

    def test_works_for_all_scenarios(self):
        """get_resolution_step should work for every scenario."""
        for sc_id in SCENARIOS:
            for decision in ("SHUTDOWN", "ISOLATION"):
                step = get_resolution_step(decision, sc_id)
                assert step.step_name == "RESOLVED"
                assert step.risk_score >= 0

    def test_timeline_event_present_in_resolution(self):
        """Every resolution should have a timeline_event."""
        for sc_id in SCENARIOS:
            for decision in ("SHUTDOWN", "ISOLATION"):
                step = SCENARIOS[sc_id].resolutions[decision]
                assert step.timeline_event is not None, (
                    f"{sc_id} {decision} resolution missing timeline_event"
                )

    def test_every_debate_message_has_required_keys(self):
        """Each debate message must have sender, role, timestamp, content, sentiment."""
        required = {"sender", "role", "timestamp", "content", "sentiment"}
        for sc_id, scenario in SCENARIOS.items():
            for step in scenario.steps:
                for msg in step.debate_messages:
                    missing = required - msg.keys()
                    assert not missing, (
                        f"{sc_id} debate message missing: {missing}"
                    )
