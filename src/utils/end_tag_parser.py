import re
from typing import List, Optional
from ..models.todo_item import ToolCall


class EndTagParser:
    END_TAG_PATTERN = r'<end></end>'

    def detect_end_tag(self, response: str) -> bool:
        if not response:
            return False
        return bool(re.search(self.END_TAG_PATTERN, response))

    def extract_content_before_end(self, response: str) -> str:
        if not response:
            return ""
        match = re.search(self.END_TAG_PATTERN, response)
        if match:
            return response[:match.start()].strip()
        return response.strip()
    
    def extract_analysis_content(self, response: str) -> str:
        """
        提取LLM的分析内容，排除工具调用部分
        
        Args:
            response: LLM的完整响应
            
        Returns:
            只包含分析内容的字符串，不包含call_tool调用
        """
        if not response:
            return ""
        
        lines = response.split('\n')
        analysis_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('call_tool('):
                continue
            analysis_lines.append(line)
        
        return '\n'.join(analysis_lines).strip()

    def parse_tool_calls(self, response: str) -> List[ToolCall]:
        tool_calls = []
        # 按行分割，逐行处理
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('call_tool('):
                continue
            
            try:
                # 简单的字符串处理方法
                if line.endswith(')'):
                    line = line[:-1]  # 去掉末尾的 )
                
                # 提取工具名（在第一个引号之间）
                first_quote = line.find('"')
                if first_quote == -1:
                    first_quote = line.find("'")
                if first_quote == -1:
                    continue
                
                second_quote = line.find('"', first_quote + 1)
                if second_quote == -1:
                    second_quote = line.find("'", first_quote + 1)
                if second_quote == -1:
                    continue
                
                tool_name = line[first_quote + 1:second_quote]
                
                # 提取参数部分（在第二个逗号之后）
                param_start = second_quote + 1
                if param_start < len(line) and line[param_start] == ',':
                    param_start += 1
                
                param_part = line[param_start:].strip()
                parameters = {}
                
                # 尝试 JSON 解析（支持单引号和双引号）
                if param_part:
                    try:
                        import json
                        # 修复单引号为双引号以符合JSON标准
                        param_json = param_part.replace("'", '"')
                        parameters = json.loads(param_json)
                    except (json.JSONDecodeError, ValueError):
                        # 如果 JSON 解析失败，尝试特殊处理 execute_query
                        if tool_name == "execute_query":
                            # 查找 sql 参数
                            sql_start = param_part.find('"sql":') 
                            if sql_start == -1:
                                sql_start = param_part.find("'sql':")
                            if sql_start != -1:
                                # 找到 SQL 字符串的开始
                                quote_pos = param_part.find('"', sql_start + 7)
                                if quote_pos == -1:
                                    quote_pos = param_part.find("'", sql_start + 7)
                                if quote_pos != -1:
                                    # 找到 SQL 字符串的结束（下一个同类型引号）
                                    end_quote = param_part.find(param_part[quote_pos], quote_pos + 1)
                                    if end_quote != -1:
                                        sql_content = param_part[quote_pos + 1:end_quote]
                                        # 处理转义字符
                                        sql_content = sql_content.replace('\\"', '"').replace("\\'", "'")
                                        parameters = {"sql": sql_content}
                
                tool_calls.append(ToolCall(
                    tool_name=tool_name,
                    parameters=parameters,
                    source="mcp"
                ))
            except Exception:
                continue
        
        return tool_calls