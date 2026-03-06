from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..utils.prompt_builder import PromptBuilder
from ..config.prompt_config import PromptConfig


class JudgeNode:
    def __init__(self, llm_client, prompt_builder: PromptBuilder):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder

    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        prompt = self.prompt_builder.build_judge_prompt_with_context(
            state['user_question'],
            state.get('collected_info', {})
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.JUDGE_ANALYZING)
        
        result = self.llm_client.chat_completion(messages)
        
        response = result['choices'][0]['message']['content']
        needs_todolist = 'YES' in response.upper()
        
        state['needs_todolist'] = needs_todolist
        state['current_mode'] = 'multi_task' if needs_todolist else 'single_task'
        
        if stream_callback:
            mode_text = PromptConfig.OutputMessages.JUDGE_MULTI_TASK if needs_todolist else PromptConfig.OutputMessages.JUDGE_SINGLE_TASK
            stream_callback(PromptConfig.OutputMessages.JUDGE_COMPLETE.format(mode=mode_text))
        
        return state