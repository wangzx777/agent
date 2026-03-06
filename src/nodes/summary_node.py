from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..utils.prompt_builder import PromptBuilder
from ..config.prompt_config import PromptConfig


class SummaryNode:
    def __init__(self, llm_client, prompt_builder: PromptBuilder):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder

    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        prompt = self.prompt_builder.build_summary_prompt(state)
        
        messages = [
            {"role": "system", "content": PromptConfig.SUMMARY_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.SUMMARY_GENERATING)
        
        result = self.llm_client.chat_completion(messages)
        summary = result['choices'][0]['message']['content']
        
        state['final_summary'] = summary
        state['task_completed'] = True
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.SUMMARY_RESULT.format(summary=summary))
        
        return state