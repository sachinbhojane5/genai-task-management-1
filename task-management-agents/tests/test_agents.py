"""Tests for ADK agents."""

import pytest


class TestAgentConfiguration:
    """Tests for agent configuration and setup."""

    def test_task_agent_config(self):
        """Test task agent is configured correctly."""
        from src.agents.task_agent.agent import task_agent

        assert task_agent.name == "task_agent"
        assert task_agent.model == "gemini-2.0-flash"
        assert len(task_agent.tools) > 0
        assert "task" in task_agent.instruction.lower()

    def test_calendar_agent_config(self):
        """Test calendar agent is configured correctly."""
        from src.agents.calendar_agent.agent import calendar_agent

        assert calendar_agent.name == "calendar_agent"
        assert calendar_agent.model == "gemini-2.0-flash"
        assert len(calendar_agent.tools) > 0
        assert "calendar" in calendar_agent.instruction.lower()

    def test_notes_agent_config(self):
        """Test notes agent is configured correctly."""
        from src.agents.notes_agent.agent import notes_agent

        assert notes_agent.name == "notes_agent"
        assert notes_agent.model == "gemini-2.0-flash"
        assert len(notes_agent.tools) > 0
        assert "note" in notes_agent.instruction.lower()

    def test_gmail_agent_config(self):
        """Test gmail agent is configured correctly."""
        from src.agents.gmail_agent.agent import gmail_agent

        assert gmail_agent.name == "gmail_agent"
        assert gmail_agent.model == "gemini-2.0-flash"
        assert len(gmail_agent.tools) > 0
        assert "email" in gmail_agent.instruction.lower()

    def test_orchestrator_has_sub_agents(self):
        """Test orchestrator agent has all sub-agents configured."""
        from src.agents.orchestrator.agent import orchestrator_agent

        assert orchestrator_agent.name == "orchestrator"
        assert len(orchestrator_agent.sub_agents) == 4

        sub_agent_names = [agent.name for agent in orchestrator_agent.sub_agents]
        assert "task_agent" in sub_agent_names
        assert "calendar_agent" in sub_agent_names
        assert "notes_agent" in sub_agent_names
        assert "gmail_agent" in sub_agent_names

    def test_root_agent_is_orchestrator(self):
        """Test root_agent is the orchestrator."""
        from src.agents.orchestrator.agent import root_agent, orchestrator_agent

        assert root_agent is orchestrator_agent


class TestAgentInstructions:
    """Tests for agent instructions content."""

    def test_orchestrator_mentions_delegation(self):
        """Test orchestrator instruction mentions delegation."""
        from src.agents.orchestrator.agent import orchestrator_agent

        instruction = orchestrator_agent.instruction.lower()
        assert "delegate" in instruction or "sub-agent" in instruction

    def test_task_agent_has_priority_guidance(self):
        """Test task agent instruction mentions priorities."""
        from src.agents.task_agent.agent import task_agent

        instruction = task_agent.instruction.lower()
        assert "priority" in instruction

    def test_calendar_agent_has_time_guidance(self):
        """Test calendar agent instruction mentions time handling."""
        from src.agents.calendar_agent.agent import calendar_agent

        instruction = calendar_agent.instruction.lower()
        assert "time" in instruction or "schedule" in instruction

    def test_gmail_agent_has_search_guidance(self):
        """Test gmail agent instruction mentions search."""
        from src.agents.gmail_agent.agent import gmail_agent

        instruction = gmail_agent.instruction.lower()
        assert "search" in instruction or "query" in instruction
