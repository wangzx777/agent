from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime
import uuid

from .todo_item import TodoItem, ToolInfo, SkillInfo, ToolResult, HistoryItem


class AgentState(TypedDict):
    session_id: str
    user_question: str
    needs_todolist: Optional[bool]
    current_mode: str
    todolist: List[TodoItem]
    current_task_index: int
    current_task: Optional[TodoItem]
    iteration_count: int
    task_history: List[HistoryItem]
    all_history: List[Dict]
    available_tools: List[ToolInfo]
    available_skills: List[SkillInfo]
    tool_results: List[ToolResult]
    task_completed: bool
    end_tag_detected: bool
    final_summary: Optional[str]
    errors: List[str]
    collected_info: Dict[str, Any]
    data_collection_completed: bool
    pending_tool_calls: Optional[List]
    conversation_history: List[Dict[str, str]]
    created_at: str
    last_updated: str


def create_initial_state(
    user_question: str,
    available_tools: List[ToolInfo],
    available_skills: List[SkillInfo] = None,
    conversation_history: List[Dict[str, str]] = None
) -> AgentState:
    now = datetime.now().isoformat()
    return AgentState(
        session_id=str(uuid.uuid4()),
        user_question=user_question,
        needs_todolist=None,
        current_mode="",
        todolist=[],
        current_task_index=0,
        current_task=None,
        iteration_count=0,
        task_history=[],
        all_history=[],
        available_tools=available_tools,
        available_skills=available_skills or [],
        tool_results=[],
        task_completed=False,
        end_tag_detected=False,
        final_summary=None,
        errors=[],
        collected_info={},
        data_collection_completed=False,
        pending_tool_calls=None,
        conversation_history=conversation_history or [],
        created_at=now,
        last_updated=now
    )


def serialize_state(state: AgentState) -> Dict[str, Any]:
    result = {}
    for key, value in state.items():
        if key == "todolist":
            result[key] = [item.to_dict() if hasattr(item, "to_dict") else item for item in value]
        elif key == "current_task":
            result[key] = value.to_dict() if value and hasattr(value, "to_dict") else value
        elif key == "available_tools":
            result[key] = [tool.to_dict() if hasattr(tool, "to_dict") else tool for tool in value]
        elif key == "available_skills":
            result[key] = [skill.to_dict() if hasattr(skill, "to_dict") else skill for skill in value]
        elif key == "tool_results":
            result[key] = [result.to_dict() if hasattr(result, "to_dict") else result for result in value]
        elif key == "task_history":
            result[key] = [item.to_dict() if hasattr(item, "to_dict") else item for item in value]
        else:
            result[key] = value
    return result


def deserialize_state(data: Dict[str, Any]) -> AgentState:
    from .todo_item import TodoItem, ToolInfo, SkillInfo, ToolResult, HistoryItem

    state = data.copy()
    if "todolist" in state:
        state["todolist"] = [TodoItem.from_dict(item) for item in state["todolist"]]
    if "current_task" in state and state["current_task"]:
        state["current_task"] = TodoItem.from_dict(state["current_task"])
    if "available_tools" in state:
        state["available_tools"] = [ToolInfo(**tool) if isinstance(tool, dict) else tool for tool in state["available_tools"]]
    if "available_skills" in state:
        state["available_skills"] = [SkillInfo(**skill) if isinstance(skill, dict) else skill for skill in state["available_skills"]]
    if "tool_results" in state:
        state["tool_results"] = [ToolResult(**result) if isinstance(result, dict) else result for result in state["tool_results"]]
    if "task_history" in state:
        state["task_history"] = [HistoryItem.from_dict(item) if isinstance(item, dict) else item for item in state["task_history"]]
    return AgentState(**state)