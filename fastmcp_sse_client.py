# fastmcp_sse_client.py
"""
FastMCP 官方客户端（异步 + async with + await）
数据库查询 MCP 服务
服务地址: http://192.168.180.37:8005/sse
"""

import asyncio
from fastmcp import Client

SSE_URL = "http://127.0.0.1:8005/sse"

async def main():
    print(f"🔌 连接到数据库查询 MCP 服务: {SSE_URL}")
    
    # 创建客户端（自动推断为 HTTP/SSE 传输）
    client = Client(SSE_URL)
    
    async with client:  # 必须使用 async with 管理连接
        try:
            # 测试连接
            await client.ping()
            print("✅ 数据库服务可达")

            # 列出可用的数据库工具
            tools = await client.list_tools()
            print(f"\n📋 可用的数据库工具 ({len(tools)} 个):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

            # 示例：获取可用表
            print("\n🔍 获取可用表...")
            tables_result = await client.call_tool("list_tables", {})
            print(f"✅ 可用表: {tables_result.data}")

            # 示例：获取表结构
            if tables_result.data and len(tables_result.data) > 0:
                table_name = tables_result.data[0]
                print(f"\n🔍 获取表结构: {table_name}")
                schema_result = await client.call_tool("get_table_schema", {"table_name": table_name})
                print(f"✅ 表结构: {schema_result.data}")

                # 示例：执行查询
                print(f"\n🔍 执行示例查询...")
                query_result = await client.call_tool(
                    "execute_query",
                    {
                        "sql": f"SELECT COUNT(*) as total FROM {table_name}"
                    }
                )
                print(f"✅ 查询结果: {query_result.data}")

        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())