from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..models.todo_item import HistoryItem
from ..utils.prompt_builder import PromptBuilder
from ..utils.end_tag_parser import EndTagParser
from ..utils.tool_call_manager import ToolCallManager
from ..config.prompt_config import PromptConfig


class ExecutorNode:
    def __init__(self, llm_client, prompt_builder: PromptBuilder, end_tag_parser: EndTagParser, tool_call_manager: ToolCallManager):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.end_tag_parser = end_tag_parser
        self.tool_call_manager = tool_call_manager

    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        state['iteration_count'] += 1
        
        prompt = self.prompt_builder.build_execution_prompt(state)
        
        messages = [
            {"role": "system", "content": PromptConfig.EXECUTION_SYSTEM.format(expert_role=self.prompt_builder.expert_role)},
            {"role": "user", "content": prompt}
        ]
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.EXECUTOR_ITERATION.format(count=state['iteration_count']))
        
        result = self.llm_client.chat_completion(messages)
        response = result['choices'][0]['message']['content']
        
        end_tag_detected = self.end_tag_parser.detect_end_tag(response)
        content = self.end_tag_parser.extract_content_before_end(response)
        
        history_item = HistoryItem(
            content=content,
            has_end_tag=end_tag_detected,
            iteration=state['iteration_count']
        )
        state['task_history'].append(history_item)
        state['end_tag_detected'] = end_tag_detected
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.EXECUTOR_RESPONSE.format(content=content))
            if end_tag_detected:
                stream_callback(PromptConfig.OutputMessages.EXECUTOR_END_TAG)
        
        if end_tag_detected and state['current_task']:
            state['current_task'].status = 'completed'
        
        await self.tool_call_manager.execute_tool_calls(state, stream_callback)
        
        return state