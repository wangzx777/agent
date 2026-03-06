import asyncio
from typing import Optional, Callable, AsyncGenerator, Union
from fastmcp import Client

from ..models.agent_state import AgentState, create_initial_state
from ..models.todo_item import ToolInfo, HistoryItem
from ..nodes.judge_node import JudgeNode
from ..nodes.planner_node import PlannerNode
from ..nodes.executor_node import ExecutorNode
from ..nodes.task_selector_node import TaskSelectorNode
from ..nodes.summary_node import SummaryNode
from ..nodes.data_collector_node import DataCollectorNode
from ..utils.prompt_builder import PromptBuilder
from ..utils.end_tag_parser import EndTagParser
from ..utils.tool_executor import ToolExecutor
from ..utils.tool_call_manager import ToolCallManager
from ..utils.routing import route_after_judge, route_after_execution, route_after_data_collection
from ..config.prompt_config import PromptConfig


class LangGraphAgent:
    def __init__(
        self,
        llm_client,
        mcp_client_or_url: Optional[Union[Client, str]] = None,
        expert_role: str = None,
        agent_instructions: str = None
    ):
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder(
            expert_role or PromptConfig.EXPERT_ROLE,
            agent_instructions or PromptConfig.AGENT_INSTRUCTIONS
        )
        self.end_tag_parser = EndTagParser()
        self.tool_executor = ToolExecutor(mcp_client_or_url)
        self.tool_call_manager = ToolCallManager(self.tool_executor, self.end_tag_parser)
        
        self.data_collector_node = DataCollectorNode(llm_client, self.prompt_builder, self.end_tag_parser, self.tool_call_manager)
        self.judge_node = JudgeNode(llm_client, self.prompt_builder)
        self.planner_node = PlannerNode(llm_client, self.prompt_builder)
        self.executor_node = ExecutorNode(llm_client, self.prompt_builder, self.end_tag_parser, self.tool_call_manager)
        self.task_selector_node = TaskSelectorNode()
        self.summary_node = SummaryNode(llm_client, self.prompt_builder)

    async def _stream_llm_response(self, messages: list) -> AsyncGenerator[str, None]:
        """流式调用LLM并返回每个chunk"""
        # 在线程中执行同步的流式调用
        def sync_stream():
            return self.llm_client.chat_completion_stream(messages)
        
        # 在线程池中执行流式调用
        loop = asyncio.get_event_loop()
        stream_gen = await loop.run_in_executor(None, sync_stream)
        
        # 逐个yield chunk
        for chunk in stream_gen:
            yield chunk
            await asyncio.sleep(0)  # 让出控制权给事件循环

    async def run(
        self,
        user_question: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        history: list = None
    ) -> AgentState:
        available_tools = await self.tool_executor.list_tools()
        
        # 提取上一个会话的问题和总结
        conversation_history = []
        if history and len(history) >= 2:
            # 获取最后一个用户问题和助手回答（总结）
            last_user_msg = None
            last_assistant_msg = None
            
            for msg in reversed(history):
                if msg.get('role') == 'user' and last_user_msg is None:
                    last_user_msg = msg.get('content', '')
                elif msg.get('role') == 'assistant' and last_assistant_msg is None:
                    last_assistant_msg = msg.get('content', '')
                
                if last_user_msg and last_assistant_msg:
                    break
            
            if last_user_msg:
                conversation_history.append({
                    'role': 'user',
                    'content': last_user_msg
                })
            if last_assistant_msg:
                conversation_history.append({
                    'role': 'assistant',
                    'content': last_assistant_msg
                })
        
        state = create_initial_state(
            user_question=user_question,
            available_tools=available_tools,
            conversation_history=conversation_history
        )
        
        if stream_callback:
            stream_callback(f"🚀 开始处理问题: {user_question}\n")
            stream_callback(f"📋 会话ID: {state['session_id']}\n")
        
        # 设置初始模式为数据收集
        state['current_mode'] = 'data_collection'
        current_node = "data_collector"
        
        while not state.get("task_completed", False):
            if current_node == "data_collector":
                state = await self.data_collector_node(state, stream_callback)
                current_node = route_after_data_collection(state)
                
                # 如果数据收集完成，清除数据收集模式
                if current_node == "judge":
                    state['current_mode'] = ''  # 将在judge节点中设置
            
            elif current_node == "judge":
                state = await self.judge_node(state, stream_callback)
                current_node = route_after_judge(state)
            
            elif current_node == "planner":
                state = await self.planner_node(state, stream_callback)
                current_node = "task_selector"
            
            elif current_node == "task_selector":
                state = await self.task_selector_node(state, stream_callback)
                if state.get("task_completed", False):
                    current_node = "summary"
                else:
                    current_node = "multi_task_executor"
            
            elif current_node == "multi_task_executor":
                state = await self.executor_node(state, stream_callback)
                current_node = route_after_execution(state)
            
            elif current_node == "single_task_executor":
                state = await self.executor_node(state, stream_callback)
                current_node = route_after_execution(state)
            
            elif current_node == "summary":
                state = await self.summary_node(state, stream_callback)
                break
        
        if stream_callback:
            stream_callback(f"\n✅ 执行完成！\n")
        
        return state

    async def run_stream(
        self,
        user_question: str,
        history: list = None
    ) -> AsyncGenerator[str, None]:
        available_tools = await self.tool_executor.list_tools()
        
        # 提取上一个会话的问题和总结
        conversation_history = []
        if history and len(history) >= 2:
            # 获取最后一个用户问题和助手回答（总结）
            last_user_msg = None
            last_assistant_msg = None
            
            for msg in reversed(history):
                if msg.get('role') == 'user' and last_user_msg is None:
                    last_user_msg = msg.get('content', '')
                elif msg.get('role') == 'assistant' and last_assistant_msg is None:
                    last_assistant_msg = msg.get('content', '')
                
                if last_user_msg and last_assistant_msg:
                    break
            
            if last_user_msg:
                conversation_history.append({
                    'role': 'user',
                    'content': last_user_msg
                })
            if last_assistant_msg:
                conversation_history.append({
                    'role': 'assistant',
                    'content': last_assistant_msg
                })
        
        state = create_initial_state(
            user_question=user_question,
            available_tools=available_tools,
            conversation_history=conversation_history
        )
        
        yield f"🚀 开始处理问题: {user_question}\n"
        yield f"📋 会话ID: {state['session_id']}\n"
        
        # 设置初始模式为数据收集
        state['current_mode'] = 'data_collection'
        current_node = "data_collector"
        
        while not state.get("task_completed", False):
            if current_node == "data_collector":
                yield "[DATA_COLLECTOR_START]\n"
                yield "🔍 正在分析是否需要收集背景信息...\n"
                
                prompt = self.data_collector_node._build_data_collection_prompt(state)
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                full_response = ""
                async for chunk in self._stream_llm_response(messages):
                    full_response += chunk
                    yield chunk
                
                end_tag_detected = self.end_tag_parser.detect_end_tag(full_response)
                content = self.end_tag_parser.extract_content_before_end(full_response)
                
                if end_tag_detected:
                    yield "\n✅ 数据收集完成\n"
                    state['data_collection_completed'] = True
                    state['pending_tool_calls'] = None
                else:
                    tool_calls = self.end_tag_parser.parse_tool_calls(full_response)
                    
                    if tool_calls:
                        state['pending_tool_calls'] = tool_calls
                        
                        from ..models.todo_item import HistoryItem
                        history_item = HistoryItem(
                            content=content,
                            has_end_tag=end_tag_detected,
                            iteration=state['iteration_count']
                        )
                        state['task_history'].append(history_item)
                        
                        await self.tool_call_manager.execute_tool_calls(state, lambda x: None)
                    elif "不需要收集额外信息" in content or "无需收集" in content:
                        yield "ℹ️ 无需收集额外背景信息\n"
                        state['data_collection_completed'] = True
                    else:
                        from ..models.todo_item import HistoryItem
                        history_item = HistoryItem(
                            content=content,
                            has_end_tag=False,
                            iteration=state['iteration_count']
                        )
                        state['task_history'].append(history_item)
                
                current_node = route_after_data_collection(state)
                
                if current_node == "data_collector":
                    yield "[DATA_COLLECTOR_CONTINUE]\n"
                    continue
                
                if current_node == "judge":
                    state['current_mode'] = ''
                    if state.get('collected_info'):
                        yield "✅ 背景信息收集完成\n"
                    else:
                        yield "ℹ️ 无需收集额外背景信息\n"
                yield "[DATA_COLLECTOR_END]\n"
            
            elif current_node == "judge":
                yield "[JUDGE_START]\n"
                yield "🤔 正在分析问题复杂度...\n"
                state = await self.judge_node(state, lambda x: None)
                mode_text = "多任务模式" if state.get("needs_todolist") else "单任务模式"
                yield f"✅ 问题分析完成，将使用 {mode_text}\n"
                current_node = route_after_judge(state)
                yield "[JUDGE_END]\n"
            
            elif current_node == "planner":
                yield "[PLANNER_START]\n"
                yield "📋 正在规划任务列表...\n"
                state = await self.planner_node(state, lambda x: None)
                yield f"✅ 规划完成，共 {len(state['todolist'])} 个任务:\n"
                for idx, task in enumerate(state['todolist'], 1):
                    yield f"  {idx}. {task.name} ({task.priority})\n"
                current_node = "task_selector"
                yield "[PLANNER_END]\n"
            
            elif current_node == "task_selector":
                yield "[TASK_SELECTOR_START]\n"
                state = await self.task_selector_node(state, lambda x: None)
                if state.get("task_completed", False):
                    current_node = "summary"
                else:
                    if state.get('current_task'):
                        yield f"\n🎯 开始执行任务: {state['current_task'].name}\n"
                        yield f"   描述: {state['current_task'].description}\n"
                    current_node = "multi_task_executor"
                yield "[TASK_SELECTOR_END]\n"
            
            elif current_node in ["multi_task_executor", "single_task_executor"]:
                yield f"[EXECUTOR_START] {current_node}\n"
                state['iteration_count'] += 1
                yield f"\n🔄 第 {state['iteration_count']} 轮执行...\n"
                
                prompt = self.prompt_builder.build_execution_prompt(state)
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                full_response = ""
                async for chunk in self._stream_llm_response(messages):
                    full_response += chunk
                    yield chunk
                
                end_tag_detected = self.end_tag_parser.detect_end_tag(full_response)
                content = self.end_tag_parser.extract_content_before_end(full_response)
                
                history_item = HistoryItem(
                    content=content,
                    has_end_tag=end_tag_detected,
                    iteration=state['iteration_count']
                )
                state['task_history'].append(history_item)
                state['end_tag_detected'] = end_tag_detected
                
                if end_tag_detected:
                    yield "\n✅ 检测到结束标签\n"
                
                if end_tag_detected and state.get('current_task'):
                    state['current_task'].status = 'completed'
                
                await self.tool_call_manager.execute_tool_calls(state, lambda x: None)
                
                current_node = route_after_execution(state)
                yield f"[EXECUTOR_END] {current_node}\n"
            
            elif current_node == "summary":
                yield "[SUMMARY_START]\n"
                yield "\n📊 正在生成总结...\n"
                
                prompt = self.prompt_builder.build_summary_prompt(state)
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                full_summary = ""
                async for chunk in self._stream_llm_response(messages):
                    full_summary += chunk
                    yield chunk
                
                state['final_summary'] = full_summary
                state['task_completed'] = True
                
                yield "[SUMMARY_END]\n"
                break
        
        yield f"\n✅ 执行完成！\n"