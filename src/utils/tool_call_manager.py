from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..utils.end_tag_parser import EndTagParser
from ..utils.tool_executor import ToolExecutor
from ..config.prompt_config import PromptConfig


class ToolCallManager:
    """工具调用管理器，负责解析和执行工具调用"""

    def __init__(self, tool_executor: ToolExecutor, end_tag_parser: EndTagParser):
        self.tool_executor = tool_executor
        self.end_tag_parser = end_tag_parser

    async def execute_tool_calls(
        self,
        state: AgentState,
        stream_callback: Optional[Callable] = None
    ) -> AgentState:
        """
        执行工具调用并更新state
        
        Args:
            state: Agent状态
            stream_callback: 流式输出回调函数
            
        Returns:
            更新后的Agent状态
        """
        tool_calls = self._get_tool_calls(state)
        
        if not tool_calls:
            return state
        
        for tool_call in tool_calls:
            if stream_callback:
                stream_callback(PromptConfig.OutputMessages.TOOL_CALL_START.format(name=tool_call.tool_name))
            
            result = await self.tool_executor.execute_tool(tool_call)
            
            if tool_call.tool_name == "execute_query" and result.success:
                sql = tool_call.parameters.get("sql", "") if isinstance(tool_call.parameters, dict) else str(tool_call.parameters)
                result.result = {
                    "sql": sql,
                    "result": result.result
                }
            
            state['tool_results'].append(result)
            
            self._store_collected_info(state, tool_call, result)
            
            if stream_callback:
                if result.success:
                    stream_callback(PromptConfig.OutputMessages.TOOL_CALL_SUCCESS)
                else:
                    stream_callback(PromptConfig.OutputMessages.TOOL_CALL_FAILED.format(error=result.error))
        
        return state
    
    def _get_tool_calls(self, state: AgentState) -> list:
        """获取待执行的工具调用"""
        if state.get("pending_tool_calls"):
            tool_calls = state["pending_tool_calls"]
            state["pending_tool_calls"] = None
            return tool_calls
        
        if state.get('task_history'):
            last_response = state['task_history'][-1].content
            return self.end_tag_parser.parse_tool_calls(last_response)
        
        return []
    
    def _store_collected_info(
        self,
        state: AgentState,
        tool_call,
        result
    ):
        """存储收集到的信息到state中"""
        if state.get("current_mode") != "data_collection" or not result.success:
            return
        
        if "collected_info" not in state:
            state["collected_info"] = {}
        
        if tool_call.tool_name == "execute_query":
            stored_value = {
                "sql": tool_call.parameters.get("sql", "") if isinstance(tool_call.parameters, dict) else str(tool_call.parameters),
                "result": result.result
            }
        else:
            stored_value = result.result
        
        if tool_call.tool_name in state["collected_info"]:
            if isinstance(state["collected_info"][tool_call.tool_name], list):
                state["collected_info"][tool_call.tool_name].append(stored_value)
            else:
                state["collected_info"][tool_call.tool_name] = [
                    state["collected_info"][tool_call.tool_name],
                    stored_value
                ]
        else:
            state["collected_info"][tool_call.tool_name] = stored_value