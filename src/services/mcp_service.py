"""
MCP (Model Context Protocol) 服务客户端
提供与MCP服务的连接和工具调用功能
"""

import asyncio
from typing import Optional, List, Any, Dict
from fastmcp import Client


class MCPService:
    """MCP服务客户端封装"""
    
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
    
    async def ping(self) -> bool:
        """测试MCP服务连接"""
        try:
            async with Client(self.mcp_url) as client:
                await client.ping()
                return True
        except Exception:
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的MCP工具列表"""
        try:
            async with Client(self.mcp_url) as client:
                tools = await client.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": getattr(tool, "input_schema", None)
                    }
                    for tool in tools
                ]
        except Exception as e:
            raise Exception(f"Failed to list MCP tools: {str(e)}")
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """调用指定的MCP工具"""
        try:
            async with Client(self.mcp_url) as client:
                result = await client.call_tool(tool_name, parameters)
                return result
        except Exception as e:
            raise Exception(f"Failed to call MCP tool '{tool_name}': {str(e)}")


async def main():
    """测试MCP服务连接（仅用于调试）"""
    from ..config import ConfigManager
    
    config_manager = ConfigManager()
    mcp_url = config_manager.get_mcp_url()
    
    print(f"🔌 连接到数据库查询 MCP 服务: {mcp_url}")
    
    mcp_service = MCPService(mcp_url)
    
    try:
        # 测试连接
        if await mcp_service.ping():
            print("✅ 数据库服务可达")
        else:
            print("❌ 数据库服务不可达")
            return

        # 列出可用的数据库工具
        tools = await mcp_service.list_tools()
        print(f"\n📋 可用的数据库工具 ({len(tools)} 个):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        # 示例：获取可用表
        if tools:
            print("\n🔍 获取可用表...")
            tables_result = await mcp_service.call_tool("list_tables", {})
            print(f"✅ 可用表: {tables_result}")

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())