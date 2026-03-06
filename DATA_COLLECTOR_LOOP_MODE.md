# 数据收集节点循环执行模式说明

## 设计目标

让数据收集节点成为一个循环执行的过程，由LLM使用MCP工具来收集数据，而不是在节点内部直接调用工具。

## 工作流程

```
用户问题 → 数据收集节点 → LLM分析是否需要收集数据
  → 不需要: 标记完成 → 判断节点
  → 需要: LLM使用call_tool调用MCP工具 → ToolCallNode执行工具
    → 结果存储到collected_info → 返回数据收集节点
    → LLM继续分析是否需要更多数据
    → 循环直到LLM输出<end></end>标签 → 判断节点
```

## 核心组件

### 1. 数据收集节点 (DataCollectorNode)

**位置**：[src/nodes/data_collector_node.py](file:///d:/work/agent2/src/nodes/data_collector_node.py)

**功能**：
- 调用LLM分析用户问题，判断是否需要收集背景信息
- 如果需要，让LLM使用 `call_tool` 调用MCP工具
- 将工具调用信息存储到 `state['pending_tool_calls']` 中
- 如果LLM输出 `<end></end>` 标签，标记数据收集完成

**系统提示词**：
```
你是数据库专家。

你的任务是分析用户问题，判断是否需要收集背景信息，如果需要，使用可用的MCP工具来收集数据。

## 工作流程
1. 分析用户问题，判断是否需要收集背景信息
2. 如果不需要收集，直接回答"不需要收集额外信息"
3. 如果需要收集，使用call_tool调用相应的MCP工具
4. 收集完所有必要信息后，在回答末尾添加<end></end>标签

## 可用工具
- list_tables(): 列出数据库中的所有表
- get_table_schema(table_name): 获取指定表的结构信息

## 重要提示
- 每次只能调用一个工具
- 如果需要调用多个工具，请分多次回答
- 收集完所有必要信息后，必须添加<end></end>标签
- 不要在数据收集阶段尝试回答用户的问题，只负责收集信息
```

### 2. 工具调用节点 (ToolCallNode)

**位置**：[src/nodes/tool_call_node.py](file:///d:/work/agent2/src/nodes/tool_call_node.py)

**增强功能**：
- 检查 `state['pending_tool_calls']`，优先处理待处理的工具调用
- 如果是数据收集模式，将工具结果存储到 `state['collected_info']` 中
- 根据工具名称自动分类存储结果：
  - `list_tables` → `collected_info['tables']`
  - `get_table_schema` → `collected_info['table_schema']`

### 3. 路由逻辑 (Routing)

**位置**：[src/utils/routing.py](file:///d:/work/agent2/src/utils/routing.py)

**新增路由函数**：

```python
def route_after_data_collection(state: AgentState) -> Literal["data_collector", "tool_call", "judge"]:
    """数据收集完成后的路由"""
    # 检查是否有待处理的工具调用
    if state.get("pending_tool_calls"):
        return "tool_call"
    
    # 检查是否检测到end标签
    if state.get("data_collection_completed"):
        return "judge"
    
    # 继续数据收集
    return "data_collector"


def route_after_tool_call(state: AgentState) -> Literal["multi_task_executor", "single_task_executor", "data_collector"]:
    """工具调用完成后的路由"""
    # 如果是数据收集模式，返回数据收集节点
    if state.get("current_mode") == "data_collection":
        return "data_collector"
    
    # 否则根据当前模式返回相应的执行节点
    if state.get("current_mode") == "multi_task":
        return "multi_task_executor"
    return "single_task_executor"
```

### 4. 状态扩展 (AgentState)

**位置**：[src/models/agent_state.py](file:///d:/work/agent2/src/models/agent_state.py)

**新增字段**：
```python
data_collection_completed: bool  # 数据收集是否完成
pending_tool_calls: Optional[List]  # 待处理的工具调用
```

## 执行示例

### 示例1：查询2024绩效为S的人

**用户问题**："查询一下2024绩效为S的人"

**执行流程**：

**第1轮 - 数据收集节点**：
```
LLM分析：需要收集表列表和表结构信息
LLM输出：call_tool("list_tables", {})
```

**第2轮 - ToolCallNode**：
```
执行工具：list_tables()
结果：['basic_info', 'performance_records', ...]
存储到：collected_info['tables']
```

**第3轮 - 数据收集节点**：
```
LLM分析：看到表列表，需要获取performance_records表的结构
LLM输出：call_tool("get_table_schema", {"table_name": "performance_records"})
```

**第4轮 - ToolCallNode**：
```
执行工具：get_table_schema("performance_records")
结果：{table_name: "performance_records", columns: [...]}
存储到：collected_info['table_schema']
```

**第5轮 - 数据收集节点**：
```
LLM分析：已有足够信息（表列表和表结构）
LLM输出：数据收集完成<end></end>
标记：data_collection_completed = True
```

**第6轮 - 判断节点**：
```
基于收集到的信息判断：单任务即可
进入：单任务执行模式
```

### 示例2：不需要收集数据的问题

**用户问题**："你好，请介绍一下你自己"

**执行流程**：

**第1轮 - 数据收集节点**：
```
LLM分析：不需要收集任何背景信息
LLM输出：不需要收集额外信息
标记：data_collection_completed = True
```

**第2轮 - 判断节点**：
```
基于收集到的信息判断：单任务即可
进入：单任务执行模式
```

## 优势

1. **LLM主导** - 由LLM决定需要收集什么信息，而不是硬编码逻辑
2. **灵活性强** - 可以适应各种不同的查询需求
3. **循环执行** - 可以多次收集信息，直到满足需求
4. **清晰标记** - 使用 `<end></end>` 标签明确表示收集完成
5. **统一接口** - 使用相同的 `call_tool` 格式，与执行阶段保持一致

## 与原设计的区别

### 原设计
```
数据收集节点 → 直接调用MCP工具 → 存储结果 → 判断节点
```
- ❌ 在节点内部直接调用工具
- ❌ 硬编码的收集逻辑
- ❌ 不够灵活

### 新设计
```
数据收集节点 → LLM使用call_tool → ToolCallNode执行 → 存储结果 → 返回数据收集节点 → 循环
```
- ✅ LLM主导收集过程
- ✅ 灵活的收集策略
- ✅ 循环执行直到完成

## 集成到主流程

```python
# LangGraphAgent.run()
state['current_mode'] = 'data_collection'
current_node = "data_collector"

while not state.get("task_completed", False):
    if current_node == "data_collector":
        state = await self.data_collector_node(state, stream_callback)
        current_node = route_after_data_collection(state)
        
        # 如果数据收集完成，清除数据收集模式
        if current_node == "judge":
            state['current_mode'] = ''  # 将在judge节点中设置
    
    elif current_node == "tool_call":
        state = await self.tool_call_node(state, stream_callback)
        current_node = route_after_tool_call(state)
    
    elif current_node == "judge":
        state = await self.judge_node(state, stream_callback)
        current_node = route_after_judge(state)
    
    # ... 其他节点
```

## 测试建议

1. **简单查询测试** - 验证不需要收集数据的情况
2. **单表查询测试** - 验证收集表结构的情况
3. **多表查询测试** - 验证收集表列表和多个表结构的情况
4. **复杂查询测试** - 验证多次循环收集的情况
5. **边界情况测试** - 验证工具调用失败等情况的处理

## 后续优化方向

1. **智能缓存** - 缓存常用的表结构信息
2. **并行收集** - 同时收集多个不相关的信息
3. **增量收集** - 根据执行过程中的需要动态收集信息
4. **收集策略优化** - 基于历史数据优化收集策略