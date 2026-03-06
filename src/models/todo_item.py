from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


@dataclass
class TodoItem:
    id: str
    name: str
    description: str
    priority: str
    status: str = "pending"

    @classmethod
    def create(cls, name: str, description: str, priority: str = "medium") -> "TodoItem":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            priority=priority,
            status="pending"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            priority=data["priority"],
            status=data.get("status", "pending")
        )


@dataclass
class ToolCall:
    tool_name: str
    parameters: Dict[str, Any]
    source: str = "mcp"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(
            tool_name=data["tool_name"],
            parameters=data["parameters"],
            source=data.get("source", "mcp")
        )


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


@dataclass
class ToolInfo:
    name: str
    description: str
    source: str = "mcp"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source
        }


@dataclass
class SkillInfo:
    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description
        }


@dataclass
class HistoryItem:
    content: str
    has_end_tag: bool = False
    iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "has_end_tag": self.has_end_tag,
            "iteration": self.iteration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryItem":
        return cls(
            content=data["content"],
            has_end_tag=data.get("has_end_tag", False),
            iteration=data.get("iteration", 0)
        )