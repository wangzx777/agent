# LangGraph Agent Framework

基于 LangGraph 的智能体框架，支持多任务规划和执行，集成 MCP 协议工具。

## 项目概述

这是一个基于 LangGraph 架构的智能体框架，专门用于数据库查询和数据分析场景。框架采用节点式设计，通过状态机的方式管理任务执行流程，支持单任务和多任务两种执行模式，并集成了 MCP (Model Context Protocol) 协议工具系统。

## 核心架构

### 整体设计思路

框架采用**状态机 + 节点式**架构，通过 `AgentState` 在不同节点之间传递状态信息。每个节点负责特定的功能，通过路由函数决定下一个执行节点。

```
用户问题
    ↓
[数据收集节点] → 循环收集背景信息
    ↓
[判断节点] → 决定执行模式
    ↓
    ├─→ [规划节点] → [任务选择节点] → [执行节点] → 循环执行
    │                                              ↓
    └─→ [执行节点] → 循环执行 → [总结节点] ←──────┘
```

### 核心组件

#### 1. 状态管理

- **AgentState**: 核心状态对象，包含会话ID、用户问题、任务列表、执行历史、工具结果等所有状态信息
- **TodoItem**: 任务项数据模型，包含任务名称、描述、优先级和状态
- **ToolInfo/ToolResult**: 工具信息和执行结果的数据模型
- **HistoryItem**: 执行历史记录，包含LLM响应内容和结束标签标记

#### 2. 节点系统

框架包含6个核心节点，每个节点负责特定的功能：

##### 数据收集节点
- **功能**: 在执行任务前，智能收集必要的背景信息（表结构、数据样本等）
- **特点**: 
  - 循环执行模式，直到收集完成或确定无需收集
  - 使用 `<end></end>` 标签判断收集完成
  - 支持模糊匹配和智能推断查询策略
- **文件**: [data_collector_node.py](file:///d:/work/agent2/src/nodes/data_collector_node.py)

##### 判断节点
- **功能**: 分析用户问题复杂度，决定是否需要分解为多个任务
- **输出**: `needs_todolist` 布尔值，决定执行模式
- **文件**: [judge_node.py](file:///d:/work/agent2/src/nodes/judge_node.py)

##### 规划节点
- **功能**: 将复杂问题分解为结构化的任务列表
- **输出**: TodoList，包含任务名称、描述和优先级
- **文件**: [planner_node.py](file:///d:/work/agent2/src/nodes/planner_node.py)

##### 任务选择节点
- **功能**: 从待执行任务中选择下一个任务
- **逻辑**: 按顺序选择pending状态的任务，标记为in_progress
- **文件**: [task_selector_node.py](file:///d:/work/agent2/src/nodes/task_selector_node.py)

##### 执行节点
- **功能**: 执行当前任务，支持工具调用和循环迭代
- **特点**:
  - 支持单任务和多任务两种模式
  - 使用 `<end></end>` 标签判断任务完成
  - 自动解析和执行工具调用
  - 记录执行历史
- **文件**: [executor_node.py](file:///d:/work/agent2/src/nodes/executor_node.py)

##### 总结节点
- **功能**: 生成最终总结，整合所有执行结果
- **输出**: 完整的总结回答
- **文件**: [summary_node.py](file:///d:/work/agent2/src/nodes/summary_node.py)

#### 3. 工具系统

##### 工具执行器
- **功能**: 执行MCP协议工具调用
- **特点**: 
  - 支持MCP 2.0协议
  - 自动处理多种返回格式
  - 支持临时连接和持久连接
- **文件**: [tool_executor.py](file:///d:/work/agent2/src/utils/tool_executor.py)

##### 工具调用管理器
- **功能**: 解析LLM响应中的工具调用并执行
- **特点**:
  - 支持灵活的工具调用格式
  - 自动存储收集的信息到状态中
  - 处理工具执行结果
- **文件**: [tool_call_manager.py](file:///d:/work/agent2/src/utils/tool_call_manager.py)

##### 结果格式化器
- **功能**: 优化工具返回结果的展示格式
- **特点**:
  - 智能识别数据类型（列表、字典、字符串）
  - 表格化展示查询结果
  - 自动截断过长的数据，减少token消耗
  - 特殊处理SQL查询结果
- **文件**: [result_formatter.py](file:///d:/work/agent2/src/utils/result_formatter.py)

#### 4. 提示词构建器

- **功能**: 为不同节点构建结构化的提示词
- **特点**:
  - 智能过滤历史记录（只保留当前循环内的内容）
  - 整合背景信息、任务列表、工具结果等多维度信息
  - 支持上下文感知的提示词构建
- **文件**: [prompt_builder.py](file:///d:/work/agent2/src/utils/prompt_builder.py)

#### 5. 结束标签解析器

- **功能**: 解析LLM响应中的 `<end></end>` 标签和工具调用
- **特点**:
  - 检测结束标签，判断任务完成
  - 提取标签前的内容
  - 解析工具调用格式
- **文件**: [end_tag_parser.py](file:///d:/work/agent2/src/utils/end_tag_parser.py)

#### 6. 路由系统

- **功能**: 根据状态决定下一个执行节点
- **路由规则**:
  - `route_after_judge`: 判断后路由（规划器或单任务执行器）
  - `route_after_data_collection`: 数据收集后路由（继续收集或判断）
  - `route_after_execution`: 执行后路由（任务选择器或总结）
- **文件**: [routing.py](file:///d:/work/agent2/src/utils/routing.py)

#### 7. 主Agent类

- **功能**: 协调所有节点，管理整体执行流程
- **特点**:
  - 支持同步和流式两种执行模式
  - 自动管理会话历史
  - 提供实时进度反馈
- **文件**: [langgraph_agent.py](file:///d:/work/agent2/src/agents/langgraph_agent.py)

## 执行流程

### 完整执行流程

1. **初始化阶段**
   - 创建初始状态
   - 获取可用工具列表
   - 提取历史对话信息

2. **数据收集阶段**
   - 分析用户问题，判断是否需要背景信息
   - 循环调用MCP工具收集数据
   - 检测 `<end></end>` 标签判断收集完成

3. **判断阶段**
   - 基于收集的背景信息，分析问题复杂度
   - 决定使用单任务模式还是多任务模式

4. **规划阶段**（仅多任务模式）
   - 将问题分解为任务列表
   - 设置任务优先级

5. **执行阶段**
   - 选择下一个待执行任务
   - 构建执行提示词（包含背景信息、历史记录、工具结果等）
   - 调用LLM获取响应
   - 解析并执行工具调用
   - 检测 `<end></end>` 标签判断任务完成
   - 循环执行直到任务完成

6. **总结阶段**
   - 整合所有执行结果
   - 生成最终总结回答

### 单任务 vs 多任务模式

#### 单任务模式
- 适用于简单、直接的问题
- 直接进入执行节点，无需规划
- 执行完成后直接进入总结

#### 多任务模式
- 适用于复杂、需要分解的问题
- 先规划任务列表，然后逐个执行
- 支持任务优先级管理
- 所有任务完成后才进入总结

## 核心特性

### 1. 智能数据收集
- 自动识别需要收集的背景信息
- 支持模糊匹配和智能推断
- 避免重复收集已获得的信息

### 2. 灵活的工具调用
- 支持MCP协议工具
- 自动解析LLM响应中的工具调用
- 支持多种工具调用格式

### 3. 历史记录管理
- 基于 `<end></end>` 标签的历史记录分段
- 智能过滤当前循环内的历史
- 支持跨会话的上下文传递

### 4. 流式输出
- 实时输出执行过程
- 支持进度反馈
- 提升用户体验

### 5. 结果优化
- 智能格式化工具返回结果
- 自动截断过长数据
- 减少token消耗

### 6. 错误处理
- 工具执行失败自动记录
- 支持重试机制
- 详细的错误信息反馈

## 项目结构

```
agent2/
├── src/
│   ├── models/              # 数据模型
│   │   ├── agent_state.py   # Agent状态定义
│   │   └── todo_item.py     # 任务项、工具信息等数据模型
│   ├── utils/               # 工具类
│   │   ├── prompt_builder.py      # 提示词构建器
│   │   ├── end_tag_parser.py      # 结束标签解析器
│   │   ├── tool_executor.py       # 工具执行器
│   │   ├── tool_call_manager.py   # 工具调用管理器
│   │   ├── result_formatter.py    # 结果格式化器
│   │   └── routing.py             # 路由函数
│   ├── nodes/               # LangGraph 节点
│   │   ├── data_collector_node.py # 数据收集节点
│   │   ├── judge_node.py          # 判断节点
│   │   ├── planner_node.py        # 规划节点
│   │   ├── task_selector_node.py  # 任务选择节点
│   │   ├── executor_node.py       # 执行节点
│   │   └── summary_node.py        # 总结节点
│   ├── agents/              # Agent 主类
│   │   └── langgraph_agent.py     # 主Agent类
│   ├── config/              # 配置管理
│   │   ├── config_manager.py      # 配置管理器
│   │   ├── prompt_config.py       # Prompt配置
│   │   ├── config.yaml            # 配置文件
│   │   └── config.template.yaml   # 配置模板
│   └── services/            # 服务层
│       └── mcp_service.py         # MCP服务
├── llm_client.py            # LLM客户端
├── gradio_app.py            # Gradio Web界面
├── example.py               # 使用示例
├── example_stream.py        # 流式输出示例
└── pyproject.toml           # 项目依赖
```

## 安装依赖

使用 uv 安装依赖：

```bash
uv pip install pyyaml requests fastmcp gradio
```

或使用 pip：

```bash
pip install pyyaml requests fastmcp gradio
```

## 快速开始

### 1. 配置应用程序

复制配置模板：

```bash
cp src/config/config.template.yaml src/config/config.yaml
```

编辑 `src/config/config.yaml` 文件：

```yaml
# LLM 配置
llm:
  api_url: "https://your-api-url.com/chat/completions"
  api_key: "your-api-key"
  model_name: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
  timeout: 120
  retry_attempts: 3
  retry_delay: 2
  stream: false

# MCP (Model Context Protocol) 配置
mcp:
  url: "http://127.0.0.1:8005/sse"
  timeout: 30
  retry_attempts: 2
```

### 2. 运行示例

运行基本示例：

```bash
python example.py
```

运行流式输出示例：

```bash
python example_stream.py
```

### 3. 使用 Gradio 界面

启动 Gradio Web 界面：

```bash
python gradio_app.py
```

然后在浏览器中打开 `http://localhost:7860`

## 使用示例

### 基本使用

```python
import asyncio
import sys
from pathlib import Path
from fastmcp import Client

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.langgraph_agent import LangGraphAgent
from llm_client import LLMClient

async def main():
    llm_client = LLMClient()
    mcp_client = Client("http://127.0.0.1:8005/sse")
    
    agent = LangGraphAgent(
        llm_client=llm_client,
        mcp_client=mcp_client,
        expert_role="数据库专家",
        agent_instructions="你是一个专业的数据库助手"
    )
    
    async with mcp_client:
        def stream_callback(content: str):
            print(content, end="", flush=True)
        
        state = await agent.run("查询数据库中有哪些表", stream_callback)
        print(f"\n会话ID: {state['session_id']}")
        print(f"执行模式: {state['current_mode']}")

asyncio.run(main())
```

### 流式输出

```python
import asyncio
import sys
from pathlib import Path
from fastmcp import Client

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.langgraph_agent import LangGraphAgent
from llm_client import LLMClient

async def main():
    llm_client = LLMClient()
    mcp_client = Client("http://127.0.0.1:8005/sse")
    
    agent = LangGraphAgent(
        llm_client=llm_client,
        mcp_client=mcp_client,
        expert_role="数据库专家",
        agent_instructions="你是一个专业的数据库助手"
    )
    
    async with mcp_client:
        async for content in agent.run_stream("查询数据库中有哪些表"):
            print(content, end="", flush=True)

asyncio.run(main())
```

## 设计亮点

### 1. 状态机架构
- 清晰的状态流转
- 易于扩展和维护
- 支持复杂的执行流程

### 2. 模块化设计
- 每个节点职责单一
- 工具类独立封装
- 便于单元测试

### 3. 智能提示词构建
- 上下文感知
- 多维度信息整合
- 历史记录智能过滤

### 4. 灵活的工具集成
- 支持MCP协议
- 自动解析工具调用
- 结果智能格式化

### 5. 用户体验优化
- 流式输出
- 实时进度反馈
- 友好的错误提示

## 更新日志

### v0.2.0 (2026-01-15)
- ✅ 完整重构README文档
- ✅ 详细说明整体架构和设计思路
- ✅ 添加核心组件说明
- ✅ 完善执行流程图

### v0.1.1 (2026-01-13)
- ✅ 修复工具执行结果未传递给 LLM 的问题
- ✅ 在提示词中添加工具执行结果部分
- ✅ 添加工具结果测试脚本

### v0.1.0 (2026-01-13)
- ✅ 完成基础框架实现
- ✅ 实现所有核心节点
- ✅ 添加 Gradio Web 界面
- ✅ 完成文档和测试

## 技术栈

- **Python 3.10+**
- **LangGraph**: 状态机框架
- **FastMCP**: MCP协议客户端
- **Gradio**: Web界面
- **PyYAML**: 配置管理
- **Requests**: HTTP客户端

## 许可证

MIT License