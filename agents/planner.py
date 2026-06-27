"""Planner Agent — 基于知识点 DAG 生成个性化学习路径，支持动态调整

核心能力:
  1. 拓扑排序 — 遵守先修关系
  2. 薄弱点优先 — weak_points 提前排
  3. 进度追踪 — 标记已完成节点
  4. 动态重规划 — 根据练习结果移除已掌握的薄弱点
  5. 个性化节奏 — 根据 pace 拆分每日任务
"""
import json
import os
import logging
from collections import deque
from .state import AgentState
from .utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是学习路径规划智能体。请根据知识点 DAG 的先修依赖关系和学生画像，生成个性化学习路径。

规划规则：
1. 遵守先修关系：必须先学完前置知识点才能进入后续知识
2. 薄弱点优先：将学生的 weak_points 相关知识点提前
3. 为薄弱点增加补充学习节点
4. 已完成节点跳过，但保留在路径中标记为 done
5. 根据学生 pace 拆分每日学习量
"""


def load_dag() -> dict:
    dag_path = os.path.join(os.path.dirname(__file__), "dag", "knowledge_dag.json")
    try:
        with open(dag_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"nodes": [], "edges": []}


def topological_sort(dag: dict, weak_points: list[str],
                     completed: list[str] | None = None) -> list[dict]:
    """
    Kahn 拓扑排序 + 薄弱点优先 + 已完成标记。

    参数:
        dag: {"nodes": [...], "edges": [...]}
        weak_points: 薄弱知识点 ID 或标题列表
        completed: 已完成的知识点 ID 列表
    返回:
        排序后的节点列表，每个节点含 priority / status / note
    """
    completed = completed or []
    nodes = {n["id"]: n for n in dag.get("nodes", [])}
    edges = dag.get("edges", [])

    adj = {nid: [] for nid in nodes}
    in_degree = {nid: 0 for nid in nodes}
    for edge in edges:
        src, tgt = edge["from"], edge["to"]
        if src in adj and tgt in adj:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    # Kahn 算法 + 薄弱点优先
    queue = deque()
    for nid, deg in in_degree.items():
        if deg == 0:
            queue.append(nid)

    path = []
    while queue:
        # 薄弱点优先出队
        weak_idx = None
        for i, nid in enumerate(queue):
            node = nodes.get(nid, {})
            if nid in weak_points or node.get("title", "") in weak_points:
                weak_idx = i
                break
        if weak_idx is not None:
            # 不能用 list.remove + index，需用 deque 的下标删除
            qlist = list(queue)
            current = qlist.pop(weak_idx)
            queue = deque(qlist)
        else:
            current = queue.popleft()

        node = dict(nodes.get(current, {"id": current, "title": current}))

        # 标记状态
        if current in completed:
            node["status"] = "done"
            node["priority"] = "low"
            node["note"] = "已完成"
        elif current in weak_points or node.get("title", "") in weak_points:
            node["status"] = "pending"
            node["priority"] = "high"
            node["note"] = "薄弱点，重点学习"
        else:
            node["status"] = "pending"
            node["priority"] = "normal"

        path.append(node)

        for neighbor in adj.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return path


def check_prerequisites(path: list[dict], dag: dict) -> list[dict]:
    """
    检验学习路径的先修关系是否满足。
    对每个节点检查：其前置节点是否都在它之前出现。
    将违反先修关系的节点标记 warning。
    """
    edges = dag.get("edges", [])
    prereq_map: dict[str, list[str]] = {}
    for edge in edges:
        prereq_map.setdefault(edge["to"], []).append(edge["from"])

    id_to_pos = {node["id"]: i for i, node in enumerate(path)}

    for node in path:
        prereqs = prereq_map.get(node["id"], [])
        violations = [
            p for p in prereqs
            if p in id_to_pos and id_to_pos[p] > id_to_pos[node["id"]]
        ]
        if violations:
            node.setdefault("warnings", [])
            node["warnings"].append(f"先修关系不满足: {violations}")

    return path


def apply_pace(path: list[dict], pace: str = "每天1小时") -> list[dict]:
    """
    根据学习节奏将路径拆分为每日任务。
    简单规则：每天 1-2 个 high 节点 或 2-3 个 normal 节点。
    """
    if "1小时" in pace or "1 小时" in pace:
        per_day_high = 1
        per_day_normal = 2
    elif "2小时" in pace or "2 小时" in pace:
        per_day_high = 2
        per_day_normal = 3
    else:
        per_day_high = 1
        per_day_normal = 2

    day = 1
    count = 0
    limit_per_day = per_day_normal

    for node in path:
        if node.get("status") == "done":
            continue
        if node.get("priority") == "high":
            limit_per_day = per_day_high
        else:
            limit_per_day = per_day_normal

        node["day"] = day
        count += 1
        if count >= limit_per_day:
            day += 1
            count = 0

    return path


def dynamic_replan(original_path: list[dict], updated_weak_points: list[str],
                   completed: list[str] | None = None) -> list[dict]:
    """
    动态重规划：根据学生做练习题后的最新掌握情况，更新路径中的薄弱点标记。

    不需要重新跑拓扑排序，直接在原路径上更新 status / priority / note。
    """
    completed = completed or []
    for node in original_path:
        nid = node.get("id", "")
        title = node.get("title", "")

        if nid in completed:
            node["status"] = "done"
            node["priority"] = "low"
            node["note"] = "已完成"
        elif nid in updated_weak_points or title in updated_weak_points:
            node["status"] = "pending"
            node["priority"] = "high"
            node["note"] = "薄弱点，重点学习"
        elif node.get("status") != "done":
            node["status"] = "pending"
            node["priority"] = "normal"
            node.pop("note", None)

    return original_path


# ── LangGraph 节点 ──

def planner_node(state: AgentState) -> AgentState:
    """规划/重规划个性化学习路径"""
    dag = load_dag()
    profile = state.get("profile") or {}
    weak_points = profile.get("weak_points", [])
    completed = state.get("completed_nodes", [])
    existing_path = state.get("learning_path", [])

    if existing_path and weak_points:
        # 已有路径 → 动态重规划
        path = dynamic_replan(existing_path, weak_points, completed)
    else:
        # 全新规划
        path = topological_sort(dag, weak_points, completed)
        path = check_prerequisites(path, dag)

    pace = profile.get("pace", "每天1小时")
    path = apply_pace(path, pace)

    # 统计
    pending = [n for n in path if n.get("status") != "done"]
    high = [n for n in pending if n.get("priority") == "high"]
    logger.info("Planner: total=%d done=%d pending=%d high_priority=%d",
                len(path), len(path) - len(pending), len(pending), len(high))

    state["learning_path"] = path
    return advance_agent(state)
