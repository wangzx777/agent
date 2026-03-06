from typing import Optional, Union
from fastmcp import Client
from ..models.todo_item import ToolCall, ToolResult, ToolInfo


class ToolExecutor:
    def __init__(self, mcp_client_or_url: Optional[Union[Client, str]] = None):
        if isinstance(mcp_client_or_url, str):
            self.mcp_url = mcp_client_or_url
            self.mcp_client = None
        else:
            self.mcp_url = None
            self.mcp_client = mcp_client_or_url

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        if not self.mcp_client and not self.mcp_url:
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error="MCP client or URL not initialized"
            )
        
        try:
            if self.mcp_client:
                # 使用传入的客户端（假设已在外部管理连接）
                result = await self.mcp_client.call_tool(
                    tool_call.tool_name,
                    tool_call.parameters
                )
            else:
                # 创建临时客户端并管理连接
                async with Client(self.mcp_url) as temp_client:
                    result = await temp_client.call_tool(
                        tool_call.tool_name,
                        tool_call.parameters
                    )
            # 处理MCP 2.0协议的返回格式
            parsed_result = None
            try:
                # 首先检查是否有 structured_content 属性（fastmcp已解析的结构化数据）
                if hasattr(result, 'structured_content') and result.structured_content:
                    parsed_result = result.structured_content.get('result', result.structured_content)
                # 检查是否有 data 属性（旧格式或错误解析）
                elif hasattr(result, 'data'):
                    parsed_result = result.data
                # 检查是否有 content 属性（MCP 2.0原始格式）
                elif hasattr(result, 'content') and result.content:
                    # MCP 2.0 返回 content 数组，第一个元素通常是文本结果
                    content_item = result.content[0]
                    if hasattr(content_item, 'text'):
                        text_content = content_item.text
                        # 如果文本内容是JSON字符串，尝试解析
                        if isinstance(text_content, str) and (text_content.strip().startswith('[') or text_content.strip().startswith('{')):
                            import json
                            parsed_result = json.loads(text_content)
                        else:
                            parsed_result = text_content
                    else:
                        parsed_result = result.content
                else:
                    # 直接使用结果对象
                    parsed_result = result
                
            except (json.JSONDecodeError, AttributeError, IndexError, TypeError) as e:
                # 如果解析失败，回退到原始结果
                parsed_result = result
            
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=True,
                result=parsed_result,
                error=None
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(e)
            )

    async def list_tools(self) -> list[ToolInfo]:
        if not self.mcp_client and not self.mcp_url:
            return []
        
        try:
            if self.mcp_client:
                tools = await self.mcp_client.list_tools()
            else:
                # 创建临时客户端并管理连接
                async with Client(self.mcp_url) as temp_client:
                    tools = await temp_client.list_tools()
            
            return [
                ToolInfo(
                    name=tool.name,
                    description=tool.description,
                    source="mcp"
                )
                for tool in tools
            ]
        except Exception:
            return []