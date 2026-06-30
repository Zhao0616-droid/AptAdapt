"""LangGraph 全局状态定义"""
from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict):
    """多智能体协同工作流共享状态"""

    # 用户信息
    user_id: str
    message: str                          # 用户当前输入
    chapter: Optional[str]                # 目标章节/知识点

    # 学生画像
    profile: Optional[Dict[str, Any]]     # 学生画像 JSON

    # 知识库检索
    retrieved_chunks: List[Dict[str, Any]]# RAG 检索结果

    # Supervisor 调度
    task_type: Optional[str]              # 任务类型
    agent_sequence: List[str]             # Agent 调用序列
    current_agent: Optional[str]          # 当前执行的 Agent

    # Worker Agent 输出
    generated_resources: List[Dict[str, Any]]  # 已生成的资源列表
    mindmap_data: Optional[str]                # 思维导图数据
    quiz_data: Optional[Dict[str, Any]]        # 题目数据
    code_data: Optional[Dict[str, Any]]        # 代码案例数据
    video_script: Optional[str]                # 视频脚本

    # Reviewer 审核
    review_passed: Optional[bool]
    review_notes: List[str]

    # 学习路径
    learning_path: List[Dict[str, Any]]
    completed_nodes: List[str]               # 已完成的知识点 ID 列表

    # ── 执行追踪 (Week 2 Monday 新增) ──
    execution_log: List[Dict[str, Any]]   # [{node, status, timestamp, duration_ms}]
    step_index: int                       # 当前步骤在 agent_sequence 中的位置
    total_steps: int                      # agent_sequence 总长度

    # 流程控制
    next_step: str                        # 下一步: supervisor / worker / reviewer / end
    error: Optional[str]                  # 错误信息
    llm_errors: List[str]                 # 大模型调用失败详情
