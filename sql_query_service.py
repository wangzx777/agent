"""
基于 FastMCP 2.0 的安全 SQL 查询 MCP 服务器（SSE 传输）

功能：
- 执行只读 SQL 查询语句（SELECT）
- 严格验证 SQL 语句，禁止任何非查询操作（INSERT, UPDATE, DELETE, DROP, ALTER 等）
- 支持 MySQL 数据库连接
- 内置安全限制，防止 SQL 注入和资源耗尽
- 自动日志记录所有查询操作，便于审计

依赖：
    uv pip install fastmcp pymysql sqlparse

启动方式：
    python sql_query_service.py [--host 0.0.0.0] [--port 8000] [--debug]

客户端连接地址示例：
    http://localhost:8000/sse   （如果 --path=/sse）
    http://localhost:8000       （如果使用默认路径）
"""

import logging
import argparse
import re
import sqlparse
from typing import List, Dict, Any, Union
from sqlparse.tokens import Keyword, DML
from fastmcp import FastMCP

# 数据库连接配置（硬编码）
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'username': 'root',
    'password': '1397775326',
    'database': 'test'
}

# 尝试导入数据库驱动
try:
    import pymysql
    DATABASE_DRIVER_AVAILABLE = True
except ImportError:
    DATABASE_DRIVER_AVAILABLE = False
    pymysql = None

# ==============================
# 配置日志系统
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SQLQueryMCP")

# ==============================
# 安全常量
# ==============================
MAX_QUERY_LENGTH = 10000        # 最大查询长度（字符数）
MAX_RESULT_ROWS = 1000          # 最大返回行数
MAX_EXECUTION_TIME = 30         # 最大执行时间（秒）

# ==============================
# SQL 安全验证函数
# ==============================

def _is_safe_sql_query(sql: str) -> bool:
    """
    验证 SQL 查询是否安全（只包含 SELECT 语句，不包含危险操作）
    
    参数:
        sql (str): 待验证的 SQL 语句
        
    返回:
        bool: 如果安全返回 True，否则返回 False
        
    异常:
        ValueError: 当 SQL 语句包含危险操作时抛出
    """
    if not isinstance(sql, str):
        raise TypeError("SQL query must be a string")
    
    # 检查查询长度
    if len(sql.strip()) == 0:
        raise ValueError("SQL query cannot be empty")
    
    if len(sql) > MAX_QUERY_LENGTH:
        raise ValueError(f"SQL query exceeds maximum length ({MAX_QUERY_LENGTH} characters)")
    
    # 使用 sqlparse 解析 SQL
    try:
        parsed = sqlparse.parse(sql)[0]
    except Exception as e:
        raise ValueError(f"Invalid SQL syntax: {e}")
    
    # 获取第一个非空白token作为语句类型
    statement_type = None
    for token in parsed.tokens:
        if not token.is_whitespace:
            statement_type = token.value.upper().strip()
            break
    
    if statement_type is None:
        raise ValueError("Unable to determine SQL statement type")
    
    # 允许的安全语句类型
    ALLOWED_STATEMENTS = {'SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN'}
    
    # 检查是否为允许的语句类型
    if statement_type not in ALLOWED_STATEMENTS:
        raise ValueError(f"Only read-only queries are allowed. Found: {statement_type}")
    
    # 额外的安全检查：禁止危险的关键字
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE',
        'EXEC', 'EXECUTE', 'CALL', 'DECLARE', 'SET', 'GRANT', 'REVOKE',
        'UNION', 'INTO', 'LOAD', 'FILE', 'OUTFILE', 'DUMPFILE',
        'REPLACE', 'MERGE', 'LOCK', 'UNLOCK', 'OPTIMIZE', 'REPAIR', 'ANALYZE'
    ]
    
    sql_upper = sql.upper()
    for keyword in dangerous_keywords:
        # 使用正则表达式确保匹配完整的单词
        if re.search(r'\b' + keyword + r'\b', sql_upper):
            raise ValueError(f"SQL query contains forbidden keyword: {keyword}")
    
    return True


def _execute_safe_query(sql: str) -> List[Dict[str, Any]]:
    """
    安全地执行 SQL 查询并返回结果
    
    参数:
        sql (str): 要执行的 SQL 查询
        
    返回:
        List[Dict[str, Any]]: 查询结果列表，每个元素是一个字典表示一行数据
    """
    if not DATABASE_DRIVER_AVAILABLE:
        raise RuntimeError("Database driver (pymysql) is not available")
    
    # 验证 SQL 查询
    _is_safe_sql_query(sql)
    
    connection = None
    cursor = None
    try:
        # 建立数据库连接
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['username'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            connect_timeout=10,
            read_timeout=MAX_EXECUTION_TIME,
            write_timeout=MAX_EXECUTION_TIME
        )
        
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 执行查询
        cursor.execute(sql)
        
        # 获取结果（限制行数）
        results = cursor.fetchmany(MAX_RESULT_ROWS)
        
        # 如果结果超过限制，记录警告
        if len(results) == MAX_RESULT_ROWS:
            logger.warning(f"Query result truncated to {MAX_RESULT_ROWS} rows")
        
        logger.info(f"Executed safe query: {sql[:100]}{'...' if len(sql) > 100 else ''}")
        return results
        
    except pymysql.Error as e:
        error_msg = f"Database error executing query: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error executing query: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==============================
# 创建 FastMCP 服务器实例
# ==============================
mcp = FastMCP(name="SQLQueryMCP")


# ==============================
# 工具定义（Tools）
# ==============================

@mcp.tool()
def execute_query(sql: str) -> List[Dict[str, Union[str, int, float, bool, None]]]:
    """
    执行安全的 SQL 查询语句（仅限 SELECT）
    
    安全措施：
        - 严格验证 SQL 语法
        - 只允许 SELECT 语句
        - 禁止所有修改数据的操作（INSERT, UPDATE, DELETE, DROP, ALTER 等）
        - 限制查询长度和结果行数
        - 限制执行时间
        - 防止 SQL 注入
        
    参数:
        sql (str): 要执行的 SQL 查询语句
        
    返回:
        List[Dict]: 查询结果，每个字典代表一行数据，键为列名，值为对应的数据
        
    示例：
        execute_query("SELECT * FROM users LIMIT 5")
        execute_query("SELECT name, email FROM customers WHERE age > 18")
    """
    if not isinstance(sql, str):
        raise TypeError("SQL query must be a string")
    
    sql = sql.strip()
    if not sql:
        raise ValueError("SQL query cannot be empty")
    
    try:
        result = _execute_safe_query(sql)
        return result
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


@mcp.tool()
def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    获取指定表的完整结构信息（列名、数据类型、是否可为空、默认值、字段注释等）
    
    参数:
        table_name (str): 表名
        
    返回:
        Dict: 包含表名和详细列信息的字典，每列包含：
            - column_name: 列名
            - data_type: 数据类型  
            - is_nullable: 是否可为空 (YES/NO)
            - column_default: 默认值
            - column_comment: 字段注释（中文说明）
            - extra: 额外信息（如 auto_increment）
        
    示例：
        get_table_schema("basic_info")
    """
    if not isinstance(table_name, str):
        raise TypeError("Table name must be a string")
    
    # 验证表名（只允许字母、数字、下划线）
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError("Invalid table name format")
    
    # 使用 information_schema 获取完整的表结构信息，包括字段注释
    sql = f"""
    SELECT 
        COLUMN_NAME as column_name,
        DATA_TYPE as data_type,
        IS_NULLABLE as is_nullable,
        COLUMN_DEFAULT as column_default,
        COLUMN_COMMENT as column_comment,
        EXTRA as extra
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}' 
    AND TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        result = _execute_safe_query(sql)
        return {
            "table_name": table_name,
            "database": DB_CONFIG['database'],
            "columns": result,
            "column_count": len(result)
        }
    except Exception as e:
        logger.error(f"Failed to get table schema for {table_name}: {e}")
        raise


@mcp.tool()
def list_tables() -> List[str]:
    """
    列出数据库中的所有表
    
    返回:
        List[str]: 表名列表
        
    示例：
        list_tables()
    """
    sql = "SHOW TABLES"
    
    try:
        result = _execute_safe_query(sql)
        # SHOW TABLES 返回的结果格式是 [{'Tables_in_database': 'table_name'}, ...]
        tables = [list(row.values())[0] for row in result]
        return tables
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise


# ==============================
# 主程序入口
# ==============================
if __name__ == "__main__":
    # 检查数据库驱动是否可用
    if not DATABASE_DRIVER_AVAILABLE:
        logger.error("Database driver (pymysql) is not installed. Please install it with: uv pip install pymysql")
        exit(1)
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(
        description="Run SQL Query MCP Server with SSE transport.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8005, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # 调整日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # 启动服务器（使用 SSE 传输）
    try:
        logger.info("Available tools: execute_query, get_table_schema, list_tables")
        logger.info(f"Connecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port,
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.error(f"Server failed to start or crashed: {e}", exc_info=True)
        raise