from typing import Literal
from ..models.agent_state import AgentState


def route_after_judge(state: AgentState) -> Literal["planner", "single_task_executor"]:
    if state.get("needs_todolist"):
        return "planner"
    return "single_task_executor"


def route_after_data_collection(state: AgentState) -> Literal["data_collector", "judge"]:
    """
    数据收集完成后的路由
    
    Returns:
        - data_collector: 继续收集数据
        - judge: 数据收集完成，进入判断节点
    """
    if state.get("data_collection_completed"):
        return "judge"
    
    return "data_collector"


def route_after_execution(state: AgentState) -> Literal["task_selector", "summary"]:
    if state.get("end_tag_detected"):
        if state.get("current_mode") == "multi_task":
            pending = [t for t in state.get("todolist", []) if t.status == "pending"]
            if pending:
                return "task_selector"
        return "summary"
    
    if state.get("current_mode") == "multi_task":
        return "multi_task_executor"
    return "single_task_executor"