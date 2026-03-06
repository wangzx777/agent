"""
结果格式化工具类
用于优化MCP返回结果的格式化，减少token消耗并提高可读性
"""

import json
from typing import Any, List, Dict, Union


class ResultFormatter:
    """结果格式化器，优化工具返回结果的展示"""
    
    # 最大显示的行数
    MAX_ROWS = 100
    # 最大显示的列数
    MAX_COLS = 15
    # 每个字段的最大长度
    MAX_FIELD_LENGTH = 300
    # 字符串结果的最大长度
    MAX_STRING_LENGTH = 50000
    
    @classmethod
    def format_result(cls, result: Any, tool_name: str = "") -> str:
        """
        格式化工具执行结果
        
        Args:
            result: 工具执行结果
            tool_name: 工具名称（用于特殊处理）
            
        Returns:
            格式化后的字符串
        """
        if result is None:
            return "无结果"
        
        # 处理字符串类型
        if isinstance(result, str):
            return cls._format_string(result)
        
        # 处理列表类型（通常是查询结果）
        if isinstance(result, list):
            return cls._format_list(result, tool_name)
        
        # 处理字典类型
        if isinstance(result, dict):
            return cls._format_dict(result, tool_name)
        
        # 其他类型直接转换为字符串
        return str(result)
    
    @classmethod
    def _format_string(cls, text: str) -> str:
        """格式化字符串结果"""
        if not text:
            return "空字符串"
        
        # 如果是JSON字符串，尝试解析并格式化
        text = text.strip()
        if text.startswith('[') or text.startswith('{'):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return cls._format_list(parsed)
                elif isinstance(parsed, dict):
                    return cls._format_dict(parsed)
            except json.JSONDecodeError:
                pass
        
        # 截断过长的字符串
        if len(text) > cls.MAX_STRING_LENGTH:
            return text[:cls.MAX_STRING_LENGTH] + "...（已截断）"
        
        return text
    
    @classmethod
    def _format_list(cls, data: List, tool_name: str = "") -> str:
        """
        格式化列表结果（通常是数据库查询结果）
        
        Args:
            data: 数据列表
            tool_name: 工具名称
            
        Returns:
            格式化的表格字符串
        """
        if not data:
            return "空结果集"
        
        # 检查是否是简单字符串列表
        if data and isinstance(data[0], (str, int, float, bool, type(None))):
            return cls._format_simple_list(data, tool_name)
        
        # 处理字典列表（数据库查询结果）
        # 获取所有字段名
        all_fields = set()
        has_dict = False
        for item in data:
            if isinstance(item, dict):
                has_dict = True
                all_fields.update(item.keys())
        
        # 如果没有字典类型的数据，直接原样输出
        if not has_dict:
            return str(data)
        
        if not all_fields:
            return f"共 {len(data)} 条记录（无字段信息）"
        
        # 限制字段数量
        fields = list(all_fields)[:cls.MAX_COLS]
        
        # 构建表格
        lines = []
        lines.append(f"共 {len(data)} 条记录")
        
        # 表头
        header = " | ".join([cls._truncate_field(f) for f in fields])
        lines.append(header)
        lines.append("-" * len(header))
        
        # 数据行（限制显示行数）
        display_rows = data[:cls.MAX_ROWS]
        for row in display_rows:
            if isinstance(row, dict):
                values = []
                for field in fields:
                    value = row.get(field, "")
                    values.append(cls._truncate_value(str(value)))
                lines.append(" | ".join(values))
        
        # 如果有更多数据，显示提示
        if len(data) > cls.MAX_ROWS:
            lines.append(f"... 还有 {len(data) - cls.MAX_ROWS} 条记录未显示")
        
        return "\n".join(lines)
    
    @classmethod
    def _format_execute_query_info(cls, data: Dict) -> str:
        """
        格式化 execute_query 的完整信息（包含SQL语句和结果）
        
        Args:
            data: 包含 sql 和 result 的字典
            
        Returns:
            格式化的字符串
        """
        lines = []
        
        # SQL语句
        sql = data.get("sql", "")
        if sql:
            lines.append("执行的SQL语句:")
            lines.append(f"```sql")
            lines.append(sql)
            lines.append("```")
            lines.append("")
        
        # 查询结果
        result = data.get("result", [])
        if result:
            lines.append("查询结果:")
            result_formatted = cls.format_result(result, "execute_query")
            lines.append(result_formatted)
        else:
            lines.append("查询结果: 无数据返回")
        
        return "\n".join(lines)
    
    @classmethod
    def _format_simple_list(cls, data: List, tool_name: str = "") -> str:
        """
        格式化简单列表（字符串、数字等）
        
        Args:
            data: 简单列表
            tool_name: 工具名称
            
        Returns:
            格式化的字符串
        """
        lines = []
        
        # 根据工具名称和列表内容选择合适的展示方式
        if tool_name == "list_tables":
            lines.append(f"共 {len(data)} 个表:")
            for item in data[:cls.MAX_ROWS]:
                lines.append(f"- {item}")
            if len(data) > cls.MAX_ROWS:
                lines.append(f"... 还有 {len(data) - cls.MAX_ROWS} 个表未显示")
        else:
            # 通用简单列表格式
            lines.append(f"共 {len(data)} 项:")
            for idx, item in enumerate(data[:cls.MAX_ROWS], 1):
                lines.append(f"{idx}. {item}")
            if len(data) > cls.MAX_ROWS:
                lines.append(f"... 还有 {len(data) - cls.MAX_ROWS} 项未显示")
        
        return "\n".join(lines)
    
    @classmethod
    def _format_dict(cls, data: Dict, tool_name: str = "", indent: int = 0) -> str:
        """
        格式化字典结果，支持嵌套结构
        
        Args:
            data: 字典数据
            tool_name: 工具名称（用于特殊处理）
            indent: 缩进级别
            
        Returns:
            格式化的字符串
        """
        if not data:
            return "空字典"
        
        # 特殊处理表结构查询结果
        if tool_name == "get_table_schema" or "columns" in data:
            return cls._format_table_schema(data)
        
        # 特殊处理 execute_query 的完整信息格式
        if tool_name == "execute_query" and "sql" in data and "result" in data:
            return cls._format_execute_query_info(data)
        
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            # 处理嵌套字典
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                nested = cls._format_dict(value, tool_name, indent + 1)
                lines.append(nested)
            # 处理列表
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # 列表中的字典，使用表格格式
                    lines.append(f"{indent_str}{key}:")
                    table_result = cls._format_list(value, tool_name)
                    # 为表格内容添加缩进
                    table_lines = table_result.split('\n')
                    for line in table_lines:
                        lines.append(f"{indent_str}  {line}")
                else:
                    # 普通列表
                    value_str = cls._truncate_value(str(value))
                    lines.append(f"{indent_str}{key}: {value_str}")
            else:
                value_str = cls._truncate_value(str(value))
                lines.append(f"{indent_str}{key}: {value_str}")
        
        return "\n".join(lines)
    
    @classmethod
    def _format_table_schema(cls, data: Dict) -> str:
        """
        格式化表结构查询结果
        
        Args:
            data: 表结构数据
            
        Returns:
            格式化的表结构字符串
        """
        lines = []
        
        # 基本信息
        if 'table_name' in data:
            lines.append(f"表名: {data['table_name']}")
        if 'database' in data:
            lines.append(f"数据库: {data['database']}")
        
        # 列信息
        if 'columns' in data and isinstance(data['columns'], list):
            columns = data['columns']
            lines.append(f"\n共 {len(columns)} 个字段:")
            
            # 表头
            header = "字段名 | 数据类型 | 可空 | 默认值 | 注释"
            lines.append(header)
            lines.append("-" * len(header))
            
            # 字段行
            for col in columns:
                if isinstance(col, dict):
                    col_name = col.get('column_name', '')
                    data_type = col.get('data_type', '')
                    is_nullable = col.get('is_nullable', '')
                    default = col.get('column_default', 'NULL') if col.get('column_default') else 'NULL'
                    comment = col.get('column_comment', '')
                    
                    line = f"{col_name} | {data_type} | {is_nullable} | {default} | {comment}"
                    lines.append(line)
        
        return "\n".join(lines)
    
    @classmethod
    def _truncate_field(cls, field: str) -> str:
        """截断字段名"""
        if len(field) > cls.MAX_FIELD_LENGTH:
            return field[:cls.MAX_FIELD_LENGTH] + "..."
        return field
    
    @classmethod
    def _truncate_value(cls, value: str) -> str:
        """截断字段值"""
        if len(value) > cls.MAX_FIELD_LENGTH:
            return value[:cls.MAX_FIELD_LENGTH] + "..."
        return value
    
    @classmethod
    def get_token_estimate(cls, formatted_result: str) -> int:
        """
        估算格式化结果的token数量（粗略估计）
        
        Args:
            formatted_result: 格式化后的字符串
            
        Returns:
            估算的token数量
        """
        # 粗略估计：中文字符约1.5 token，英文单词约1 token
        chinese_chars = len([c for c in formatted_result if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(formatted_result) - chinese_chars
        
        return int(chinese_chars * 1.5 + other_chars * 0.5)