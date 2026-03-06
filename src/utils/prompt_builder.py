from typing import List, Optional, Dict
from ..models.agent_state import AgentState
from ..models.todo_item import ToolInfo, SkillInfo, HistoryItem
from .result_formatter import ResultFormatter
from ..config.prompt_config import PromptConfig


class PromptBuilder:
    def __init__(self, expert_role: str = None, agent_instructions: str = ""):
        self.expert_role = expert_role or PromptConfig.EXPERT_ROLE
        self.agent_instructions = agent_instructions

    def _filter_current_loop_history(self, task_history: List[HistoryItem]) -> List[HistoryItem]:
        """
        过滤历史记录，只保留当前循环内的内容（上一个end标签之后的所有内容）
        
        Args:
            task_history: 完整的历史记录列表
            
        Returns:
            当前循环内的历史记录列表
        """
        if not task_history:
            return []
        
        # 从后往前找，找到最后一个包含end标签的历史项
        last_end_index = -1
        for i in range(len(task_history) - 1, -1, -1):
            if task_history[i].has_end_tag:
                last_end_index = i
                break
        
        # 如果找到了end标签，返回该标签之后的所有历史记录
        if last_end_index != -1:
            return task_history[last_end_index + 1:]
        
        # 如果没有找到end标签，返回所有历史记录
        return task_history

    def build_execution_prompt(
        self,
        state: AgentState,
        include_history: bool = True
    ) -> str:
        prompt_parts = []
        
        background_info = self._build_background_info(state)
        task_list = self._build_task_list(state)
        current_task = self._build_current_task(state)
        available_tools = self._build_available_tools(state)
        available_skills = self._build_available_skills(state)
        history = self._build_history(state, include_history)
        tool_results = self._build_tool_results(state)
        conversation_history = self._build_conversation_history(state)
        
        return PromptConfig.EXECUTION_PROMPT.format(
            expert_role=self.expert_role,
            agent_instructions=self.agent_instructions,
            user_question=state['user_question'],
            background_info=background_info,
            task_list=task_list,
            current_task=current_task,
            available_tools=available_tools,
            available_skills=available_skills,
            history=history,
            tool_results=tool_results,
            conversation_history=conversation_history
        )
    
    def _build_background_info(self, state: AgentState) -> str:
        if not state.get('collected_info'):
            return ""
        
        parts = ["## 背景信息"]
        
        if 'tables' in state['collected_info']:
            parts.append("### 可用表列表")
            formatted_tables = ResultFormatter.format_result(state['collected_info']['tables'], "list_tables")
            parts.append(formatted_tables)
            parts.append("")
        
        if 'table_schema' in state['collected_info']:
            parts.append("### 表结构信息")
            formatted_schema = ResultFormatter.format_result(state['collected_info']['table_schema'], "get_table_schema")
            parts.append(formatted_schema)
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_task_list(self, state: AgentState) -> str:
        if state['current_mode'] != 'multi_task' or not state['todolist']:
            return ""
        
        parts = ["## 任务列表"]
        for idx, task in enumerate(state['todolist'], 1):
            status_icon = "✓" if task.status == "completed" else "○" if task.status == "in_progress" else "○"
            parts.append(f"{idx}. [{status_icon}] {task.name} (优先级: {task.priority})")
            parts.append(f"   描述: {task.description}")
        parts.append("")
        
        return "\n".join(parts)
    
    def _build_current_task(self, state: AgentState) -> str:
        if not state['current_task']:
            return ""
        
        return f"## 当前任务\n任务名称: {state['current_task'].name}\n任务描述: {state['current_task'].description}\n"
    
    def _build_available_tools(self, state: AgentState) -> str:
        if not state['available_tools']:
            return ""
        
        parts = ["## 可用工具"]
        for tool in state['available_tools']:
            parts.append(f"- {tool.name}: {tool.description}")
        parts.append("")
        
        return "\n".join(parts)
    
    def _build_available_skills(self, state: AgentState) -> str:
        if not state['available_skills']:
            return ""
        
        parts = ["## 可用技能"]
        for skill in state['available_skills']:
            parts.append(f"- {skill.name}: {skill.description}")
        parts.append("")
        
        return "\n".join(parts)
    
    def _build_history(self, state: AgentState, include_history: bool) -> str:
        if not include_history or not state['task_history']:
            return ""
        
        current_loop_history = self._filter_current_loop_history(state['task_history'])
        if not current_loop_history:
            return ""
        
        parts = ["## 历史记录"]
        for history_item in current_loop_history:
            parts.append(f"第{history_item.iteration}轮:\n{history_item.content}\n")
        
        return "\n".join(parts)
    
    def _build_tool_results(self, state: AgentState) -> str:
        if not state['tool_results']:
            return ""
        
        parts = ["## 工具执行结果"]
        for idx, result in enumerate(state['tool_results'], 1):
            status = "成功" if result.success else "失败"
            parts.append(f"{idx}. 工具: {result.tool_name}")
            parts.append(f"   状态: {status}")
            if result.success:
                formatted_result = ResultFormatter.format_result(result.result, result.tool_name)
                parts.append(f"   结果:\n{formatted_result}")
            else:
                parts.append(f"   错误: {result.error}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _build_conversation_history(self, state: AgentState) -> str:
        if not state.get('conversation_history'):
            return ""
        
        parts = ["## 上一个会话"]
        for msg in state['conversation_history']:
            role = "用户问题" if msg.get('role') == 'user' else "助手总结"
            parts.append(f"{role}:\n{msg.get('content', '')}\n")
        
        return "\n".join(parts)

    def build_judge_prompt(self, user_question: str) -> str:
        return PromptConfig.JUDGE_PROMPT.format(user_question=user_question)
    
    def build_judge_prompt_with_context(self, user_question: str, collected_info: Dict) -> str:
        collected_info_str = self._format_collected_info(collected_info)
        return PromptConfig.JUDGE_PROMPT_WITH_CONTEXT.format(
            user_question=user_question,
            collected_info=collected_info_str
        )
    
    def _format_collected_info(self, collected_info: Dict) -> str:
        if not collected_info:
            return ""
        
        parts = []
        
        for key, value in collected_info.items():
            if key == 'tables':
                parts.append("### 可用表列表")
                formatted_tables = ResultFormatter.format_result(value, "list_tables")
                parts.append(formatted_tables)
                parts.append("")
            elif key == 'table_schema':
                parts.append("### 表结构信息")
                formatted_schema = ResultFormatter.format_result(value, "get_table_schema")
                parts.append(formatted_schema)
                parts.append("")
            else:
                parts.append(f"### {key} 执行结果")
                try:
                    formatted_result = ResultFormatter.format_result(value, key)
                    parts.append(formatted_result)
                except:
                    parts.append(str(value))
                parts.append("")
        
        return "\n".join(parts)

    def build_planner_prompt(self, user_question: str, available_tools: List[ToolInfo]) -> str:
        available_tools_str = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])
        return PromptConfig.PLANNER_PROMPT.format(
            user_question=user_question,
            available_tools=available_tools_str
        )
    
    def build_planner_prompt_with_context(self, user_question: str, available_tools: List[ToolInfo], collected_info: Dict) -> str:
        collected_info_str = self._format_collected_info(collected_info)
        available_tools_str = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])
        return PromptConfig.PLANNER_PROMPT_WITH_CONTEXT.format(
            user_question=user_question,
            collected_info=collected_info_str,
            available_tools=available_tools_str
        )

    def build_summary_prompt(self, state: AgentState) -> str:
        completed_tasks = ""
        if state['todolist']:
            for task in state['todolist']:
                if task.status == "completed":
                    completed_tasks += f"- {task.name}: 已完成\n"
        
        tool_results_summary = ""
        if state['tool_results']:
            tool_results_summary = "工具调用结果:\n"
            for idx, result in enumerate(state['tool_results'], 1):
                status = "成功" if result.success else "失败"
                tool_results_summary += f"{idx}. 工具: {result.tool_name}\n"
                tool_results_summary += f"   状态: {status}\n"
                if result.success and result.result is not None:
                    formatted_result = ResultFormatter.format_result(result.result, result.tool_name)
                    tool_results_summary += f"   结果:\n{formatted_result}\n"
                elif result.error:
                    tool_results_summary += f"   错误: {result.error}\n"
                tool_results_summary += "\n"
        
        return PromptConfig.SUMMARY_PROMPT.format(
            user_question=state['user_question'],
            current_mode=state['current_mode'],
            completed_tasks=completed_tasks,
            iteration_count=state['iteration_count'],
            tool_results_summary=tool_results_summary
        )