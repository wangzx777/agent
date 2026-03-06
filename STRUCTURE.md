# 项目结构

```
agent2/
│
├── src/                          # 源代码目录
│   ├── __init__.py
│   │
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── todo_item.py         # TodoItem, ToolCall, ToolResult 等
│   │   ├── agent_state.py       # AgentState 状态定义
│   │   └── models.py            # 模型导出
│   │
│   ├── utils/                    # 工具类
│   │   ├── __init__.py
│   │   ├── end_tag_parser.py    # 结束标签解析器
│   │   ├── prompt_builder.py    # 提示词构建器
│   │   ├── tool_executor.py     # 工具执行器
│   │   ├── routing.py           # 路由函数
│   │   └── utils.py             # 工具导出
│   │
│   ├── nodes/                    # LangGraph 节点
│   │   ├── __init__.py
│   │   ├── judge_node.py        # 判断节点
│   │   ├── planner_node.py      # 规划器节点
│   │   ├── executor_node.py     # 执行节点
│   │   ├── task_selector_node.py # 任务选择节点
│   │   ├── tool_call_node.py    # 工具调用节点
│   │   ├── summary_node.py      # 总结节点
│   │   └── nodes.py             # 节点导出
│   │
│   ├── agents/                   # Agent 主类
│   │   ├── __init__.py
│   │   ├── langgraph_agent.py   # LangGraphAgent 主类
│   │   └── agents.py            # Agent 导出
│   │
│   └── config/                   # 配置管理
│       ├── __init__.py
│       ├── config_manager.py    # 配置管理器
│       └── config.py            # 配置导出
│
├── llm_client.py                 # LLM 客户端（已提供）
├── fastmcp_sse_client.py         # MCP 客户端示例（已提供）
├── llm_config.yaml               # LLM 配置文件（已提供）
│
├── example.py                    # 基本使用示例
├── example_stream.py             # 流式输出示例
├── test_basic.py                 # 基础单元测试
├── gradio_app.py                 # Gradio Web 界面
├── start_gradio.bat              # Gradio 启动脚本（Windows）
│
├── pyproject.toml                # 项目依赖配置
├── README.md                     # 项目文档
├── PROJECT_SUMMARY.md            # 项目实现总结
├── GRADIO_GUIDE.md               # Gradio 使用说明
├── QUICKSTART.md                 # 快速启动指南
├── design.md                     # 设计文档（已提供）
└── STRUCTURE.md                  # 本文件
```

## 模块说明

### src/models/
数据模型定义，包含所有核心数据结构：
- `TodoItem`: 任务项，包含 id、name、description、priority、status
- `ToolCall`: 工具调用，包含 tool_name、parameters、source
- `ToolResult`: 工具结果，包含 tool_name、success、result、error
- `ToolInfo`: 工具信息，包含 name、description、source
- `SkillInfo`: 技能信息，包含 name、description
- `AgentState`: Agent 状态，包含所有执行上下文

### src/utils/
工具类和辅助函数：
- `EndTagParser`: 解析 `<end></end>` 标签和工具调用
- `PromptBuilder`: 构建各种提示词
- `ToolExecutor`: 执行 MCP 工具调用
- `Routing`: 定义节点之间的路由逻辑

### src/nodes/
LangGraph 节点实现：
- `JudgeNode`: 判断问题复杂度
- `PlannerNode`: 生成任务列表
- `ExecutorNode`: 执行任务
- `TaskSelectorNode`: 选择下一个任务
- `ToolCallNode`: 处理工具调用
- `SummaryNode`: 生成总结

### src/agents/
Agent 主类：
- `LangGraphAgent`: 核心执行引擎，协调所有节点

### src/config/
配置管理：
- `ConfigManager`: 加载和管理配置

## 执行流程

```
用户输入问题
    ↓
[JudgeNode] 判断是否需要 TodoList
    ↓
    ├─→ YES → [PlannerNode] 生成任务列表
    │           ↓
    │       [TaskSelectorNode] 选择任务
    │           ↓
    └─→ NO → 直接执行
            ↓
        [ExecutorNode] 执行任务
            ↓
        检测 <end></end> 标签
            ↓
    ┌───────┴───────┐
    ↓               ↓
有标签           无标签
    ↓               ↓
[ToolCallNode] → [ExecutorNode]
    ↓
检查是否还有任务
    ↓
    ├─→ 有 → [TaskSelectorNode]
    └─→ 无 → [SummaryNode]
            ↓
        结束
```

## 使用方式

### 1. 基本使用
```bash
python example.py
```

### 2. 流式输出
```bash
python example_stream.py
```

### 3. Gradio Web 界面
```bash
python gradio_app.py
```
或双击 `start_gradio.bat`（Windows）

然后在浏览器中打开 `http://localhost:7860`

### 4. 运行测试
```bash
python test_basic.py
```

## 依赖安装

```bash
uv pip install pyyaml requests fastmcp gradio
```

或

```bash
pip install pyyaml requests fastmcp
```