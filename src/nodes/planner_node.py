import re
from typing import Callable, Optional
from ..models.agent_state import AgentState
from ..models.todo_item import TodoItem
from ..utils.prompt_builder import PromptBuilder
from ..config.prompt_config import PromptConfig


class PlannerNode:
    def __init__(self, llm_client, prompt_builder: PromptBuilder):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder

    async def __call__(self, state: AgentState, stream_callback: Optional[Callable] = None) -> AgentState:
        prompt = self.prompt_builder.build_planner_prompt_with_context(
            state['user_question'],
            state['available_tools'],
            state.get('collected_info', {})
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.PLANNER_PLANNING)
        
        result = self.llm_client.chat_completion(messages)
        response = result['choices'][0]['message']['content']
        
        todolist = self._parse_todolist(response, state['user_question'])
        state['todolist'] = todolist
        
        if stream_callback:
            stream_callback(PromptConfig.OutputMessages.PLANNER_COMPLETE.format(count=len(todolist)))
            for idx, task in enumerate(todolist, 1):
                stream_callback(f"  {idx}. {task.name} ({task.priority})\n")
        
        return state

    def _parse_todolist(self, response: str, user_question: str) -> list[TodoItem]:
        todolist = []
        pattern = r'任务(\d+):\s*(.+?)\n描述:\s*(.+?)\n优先级:\s*(\w+)'
        matches = re.findall(pattern, response)
        
        for match in matches:
            _, name, description, priority = match
            todolist.append(TodoItem.create(
                name=name.strip(),
                description=description.strip(),
                priority=priority.strip().lower()
            ))
        
        if not todolist:
            todolist.append(TodoItem.create(
                name="执行任务",
                description=user_question,
                priority="medium"
            ))
        
        return todolist