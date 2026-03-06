from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..utils.prompt_builder import PromptBuilder
from ..config.prompt_config import PromptConfig


class TaskSelectorNode:
    def __init__(self):
        pass

    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        pending_tasks = [t for t in state['todolist'] if t.status == 'pending']
        
        if not pending_tasks:
            state['task_completed'] = True
            return state
        
        next_task = pending_tasks[0]
        next_task.status = 'in_progress'
        
        state['current_task'] = next_task
        state['current_task_index'] = state['todolist'].index(next_task)
        state['task_history']: list = []
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.TASK_SELECTOR_START.format(name=next_task.name))
            stream_callback(PromptConfig.OutputMessages.TASK_SELECTOR_DESC.format(description=next_task.description))
        
        return state