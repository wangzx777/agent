"""
数据收集节点（循环执行模式）
让LLM使用MCP工具来收集数据，直到收集完成
"""

from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..utils.prompt_builder import PromptBuilder
from ..utils.end_tag_parser import EndTagParser
from ..utils.result_formatter import ResultFormatter
from ..utils.tool_call_manager import ToolCallManager
from ..config.prompt_config import PromptConfig


class DataCollectorNode:
    """数据收集节点，让LLM使用MCP工具收集数据"""
    
    def __init__(self, llm_client, prompt_builder: PromptBuilder, end_tag_parser: EndTagParser, tool_call_manager: ToolCallManager):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.end_tag_parser = end_tag_parser
        self.tool_call_manager = tool_call_manager
    
    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        """
        数据收集节点（循环执行模式）
        
        工作流程：
        1. 构建数据收集提示词
        2. 调用LLM，让LLM决定是否需要收集数据以及如何收集
        3. 如果LLM决定调用工具，解析工具调用并执行
        4. 如果LLM输出<end></end>标签，标记数据收集完成
        """
        
        if not state.get('task_history'):
            if stream_callback:
                stream_callback(PromptConfig.OutputMessages.DATA_COLLECTOR_START)
        
        prompt = self._build_data_collection_prompt(state)
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        full_response = ""
        
        for chunk in self.llm_client.chat_completion_stream(messages):
            full_response += chunk
            
            if stream_callback:
                stream_callback(chunk)
        
        if self.end_tag_parser.detect_end_tag(full_response):
            if stream_callback:
                stream_callback(PromptConfig.OutputMessages.DATA_COLLECTOR_COMPLETE)
            state['data_collection_completed'] = True
            state['pending_tool_calls'] = None
            return state
        
        tool_calls = self.end_tag_parser.parse_tool_calls(full_response)
        
        if tool_calls:
            state['pending_tool_calls'] = tool_calls
            
            from ..models.todo_item import HistoryItem
            content = self.end_tag_parser.extract_content_before_end(full_response)
            history_item = HistoryItem(
                content=content,
                has_end_tag=self.end_tag_parser.detect_end_tag(full_response),
                iteration=state['iteration_count']
            )
            state['task_history'].append(history_item)
            
            await self.tool_call_manager.execute_tool_calls(state, stream_callback)
            
            return state
        
        content = self.end_tag_parser.extract_content_before_end(full_response)
        if "不需要收集额外信息" in content or "无需收集" in content:
            if stream_callback:
                stream_callback(PromptConfig.OutputMessages.DATA_COLLECTOR_NO_NEED)
            state['data_collection_completed'] = True
            return state
        
        from ..models.todo_item import HistoryItem
        history_item = HistoryItem(
            content=content,
            has_end_tag=False,
            iteration=state['iteration_count']
        )
        state['task_history'].append(history_item)
        
        return state
    
    def _build_system_prompt(self) -> str:
        return PromptConfig.DATA_COLLECTOR_SYSTEM.format(expert_role=self.prompt_builder.expert_role)
    
    def _build_data_collection_prompt(self, state: AgentState) -> str:
        prompt_parts = []
        
        system_content = PromptConfig.DATA_COLLECTOR_SYSTEM.format(expert_role=self.prompt_builder.expert_role)
        prompt_parts.append(system_content)
        prompt_parts.append("")
        
        prompt_parts.append("## 可用工具")
        if state.get('available_tools'):
            for tool in state['available_tools']:
                prompt_parts.append(f"- {tool.name}: {tool.description}")
        prompt_parts.append("")
        
        prompt_parts.append("## 已收集的信息")
        if state.get('collected_info'):
            if 'tables' in state['collected_info']:
                prompt_parts.append("### 可用表列表")
                formatted_tables = ResultFormatter.format_result(state['collected_info']['tables'], "list_tables")
                prompt_parts.append(formatted_tables)
                prompt_parts.append("")
            
            if 'table_schema' in state['collected_info']:
                prompt_parts.append("### 表结构信息")
                formatted_schema = ResultFormatter.format_result(state['collected_info']['table_schema'], "get_table_schema")
                prompt_parts.append(formatted_schema)
                prompt_parts.append("")
        
        prompt_parts.append("## 工具执行结果")
        if state.get('tool_results'):
            for idx, result in enumerate(state.get('tool_results', []), 1):
                status = "成功" if result.success else "失败"
                prompt_parts.append(f"{idx}. 工具: {result.tool_name}")
                prompt_parts.append(f"   状态: {status}")
                if result.success:
                    formatted_result = ResultFormatter.format_result(result.result, result.tool_name)
                    prompt_parts.append(f"   结果:\n{formatted_result}")
                else:
                    prompt_parts.append(f"   错误: {result.error}")
                prompt_parts.append("")
        
        prompt_parts.append("## 历史记录")
        if state.get('task_history'):
            for history_item in state['task_history']:
                prompt_parts.append(f"第{history_item.iteration}轮:\n{history_item.content}\n")
        
        prompt_parts.append("## 上一个会话")
        if state.get('conversation_history'):
            for msg in state['conversation_history']:
                role = "用户问题" if msg.get('role') == 'user' else "助手总结"
                prompt_parts.append(f"{role}:\n{msg.get('content', '')}\n")
        
        task_content = PromptConfig.DATA_COLLECTOR_TASK.format(user_question=state['user_question'])
        prompt_parts.append(task_content)
        
        return "\n".join(prompt_parts)