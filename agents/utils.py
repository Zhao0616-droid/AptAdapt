"""Shared helpers for agent workflow state."""
from .state import AgentState


def next_in_sequence(state: AgentState) -> str:
    """Return the next node in agent_sequence after current next_step."""
    seq = state.get("agent_sequence", [])
    current = state.get("next_step", "")
    if current in seq:
        idx = seq.index(current)
        return seq[idx + 1] if idx + 1 < len(seq) else "end"
    return "end"


def advance_agent(state: AgentState) -> AgentState:
    """Advance next_step to the next agent."""
    state["current_agent"] = state.get("next_step", "")
    state["next_step"] = next_in_sequence(state)
    return state


def record_llm_error(state: AgentState, agent: str, error: Exception) -> None:
    """Keep provider failures visible instead of hiding them behind fallback content."""
    errors = state.get("llm_errors", [])
    errors.append(f"{agent}: {error}")
    state["llm_errors"] = errors
    state["error"] = str(error)
