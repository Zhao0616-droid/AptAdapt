"""Agent 共享工具函数"""
from .state import AgentState


def next_in_sequence(state: AgentState) -> str:
    """
    根据 agent_sequence 和当前 next_step（即当前节点名），
    返回序列中的下一个节点名。无后续节点返回 'end'。
    """
    seq = state.get("agent_sequence", [])
    current = state.get("next_step", "")
    if current in seq:
        idx = seq.index(current)
        return seq[idx + 1] if idx + 1 < len(seq) else "end"
    return "end"


def advance_agent(state: AgentState) -> AgentState:
    """将 state 的 next_step 推进到序列中的下一个 agent，并更新 current_agent"""
    state["current_agent"] = state.get("next_step", "")
    state["next_step"] = next_in_sequence(state)
    return state
