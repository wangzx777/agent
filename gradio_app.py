import asyncio
import sys
from pathlib import Path
import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.langgraph_agent import LangGraphAgent
from src.config import ConfigManager
from llm_client import LLMClient


class GradioAgentInterface:
    def __init__(self):
        self.llm_client = LLMClient()
        self.agent = None
        self.is_initialized = False

    async def initialize(self):
        if not self.is_initialized:
            # 从配置管理器获取MCP URL
            config_manager = ConfigManager()
            mcp_url = config_manager.get_mcp_url()
            
            self.agent = LangGraphAgent(
                llm_client=self.llm_client,
                mcp_client_or_url=mcp_url
            )
            self.is_initialized = True

    async def close(self):
        # 不再需要关闭 MCP 客户端，因为每次调用都会创建临时连接
        self.is_initialized = False

interface = GradioAgentInterface()


def run_agent_stream(user_question: str, history: list):
    """流式运行agent，直接yield内容"""
    if not user_question or not user_question.strip():
        error_msg = "请输入问题"
        error_history = history + [
            {"role": "user", "content": user_question},
            {"role": "assistant", "content": error_msg}
        ]
        yield error_history, "❌ 输入为空"
        return
    
    try:
        # 在同步上下文中运行异步初始化
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_async():
            await interface.initialize()
            
            full_response = ""
            # 创建新的历史记录
            new_history = history + [{"role": "user", "content": user_question}]
            
            # 运行流式agent，传入历史对话
            async_gen = interface.agent.run_stream(user_question, history)
            
            while True:
                try:
                    # 获取下一个chunk
                    content = await async_gen.__anext__()
                    full_response += content
                    
                    # 更新历史记录
                    current_history = new_history + [{"role": "assistant", "content": full_response}]
                    yield current_history, "🔄 执行中..."
                    
                except StopAsyncIteration:
                    # 流式完成
                    final_history = new_history + [{"role": "assistant", "content": full_response}]
                    yield final_history, "✅ 执行成功"
                    break
        
        # 运行异步生成器
        async_gen = run_async()
        
        while True:
            try:
                result = loop.run_until_complete(async_gen.__anext__())
                yield result
            except StopAsyncIteration:
                break
                
    except Exception as e:
        error_msg = f"❌ 执行失败: {str(e)}"
        error_history = history + [
            {"role": "user", "content": user_question},
            {"role": "assistant", "content": error_msg}
        ]
        yield error_history, error_msg
    finally:
        try:
            loop.close()
        except:
            pass


def clear_chat():
    return "", [], "就绪"


with gr.Blocks(title="LangGraph Agent 测试界面", analytics_enabled=False) as demo:
    demo.queue()
    gr.Markdown("# 🤖 LangGraph Agent 测试界面")
    gr.Markdown("基于 LangGraph 的智能体框架，支持多任务规划和执行，集成 MCP 协议工具。")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="对话历史",
                height=500,
                show_copy_button=True,
                type="messages"
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    label="输入问题",
                    placeholder="请输入你的问题，例如：查询数据库中有哪些表",
                    scale=4
                )
                submit_btn = gr.Button("发送", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("清空对话", variant="secondary")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 使用说明")
            gr.Markdown("""
            1. 在输入框中输入你的问题
            2. 点击"发送"按钮执行
            3. Agent 会自动分析问题并执行
            4. 支持流式输出执行过程
            
            ### 示例问题
            - 查询数据库中有哪些表
            - 统计每个表的记录数
            - 查询用户表的前10条记录
            """)
            
            status_output = gr.Textbox(
                label="执行状态",
                value="就绪",
                interactive=False
            )
    
    submit_btn.click(
        fn=run_agent_stream,
        inputs=[user_input, chatbot],
        outputs=[chatbot, status_output],
        queue=True
    ).then(
        lambda: "",
        outputs=[user_input]
    )
    
    user_input.submit(
        fn=run_agent_stream,
        inputs=[user_input, chatbot],
        outputs=[chatbot, status_output],
        queue=True
    ).then(
        lambda: "",
        outputs=[user_input]
    )
    
    clear_btn.click(
        fn=clear_chat,
        outputs=[user_input, chatbot, status_output]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )