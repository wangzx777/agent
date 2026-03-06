"""
LLM客户端 - 数据库智能问答助手专用
"""
import requests
import json
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator


class ConfigManager:
    def __init__(self, config_path: str = "src/config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_llm_config(self) -> "LLMConfig":
        # 从嵌套的 llm 配置中提取参数
        llm_config = self.config.get('llm', {})
        llm_params = {
            'api_url': llm_config.get('api_url'),
            'api_key': llm_config.get('api_key'),
            'model_name': llm_config.get('model_name'),
            'temperature': llm_config.get('temperature', 0.7),
            'max_tokens': llm_config.get('max_tokens', 2000),
            'timeout': llm_config.get('timeout', 120),
            'retry_attempts': llm_config.get('retry_attempts', 3),
            'retry_delay': llm_config.get('retry_delay', 2),
            'stream': llm_config.get('stream', False)
        }
        return LLMConfig(**llm_params)


class LLMConfig:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 120,
        retry_attempts: int = 3,
        retry_delay: int = 2,
        stream: bool = False
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.stream = stream


class AgentLogger:
    def __init__(self):
        pass
    
    def log_thought_process(self, message: str):
        pass


SYSTEM_PROMPT = "你是一个专业的数据库助手。"
QUESTION_ANALYSIS_PROMPT = "分析问题: {user_question}"
SQL_GENERATION_PROMPT = "生成SQL: {user_question}"
PERFORMANCE_OPTIMIZATION_PROMPT = "优化SQL: {sql_query}"
DATABASE_DESIGN_PROMPT = "设计数据库: {user_question}"
TROUBLESHOOTING_PROMPT = "排查问题: {user_question}"


class LLMClient:
    """LLM客户端 - 数据库智能问答助手专用"""
    
    def __init__(self, logger: Optional[AgentLogger] = None, stream_callback=None):
        self.config_manager = ConfigManager()
        self.llm_config = self.config_manager.get_llm_config()
        self.logger = logger
        self.stream_callback = stream_callback
        
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        调用LLM聊天完成API（非流式）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            API响应结果
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_config.api_key}"
        }
        
        payload = {
            "model": self.llm_config.model_name,
            "messages": messages,
            "temperature": temperature or self.llm_config.temperature,
            "max_tokens": max_tokens or self.llm_config.max_tokens,
            "stream": False  # chat_completion 始终使用非流式
        }
        
        # 重试机制
        for attempt in range(self.llm_config.retry_attempts):
            try:
                if self.logger:
                    self.logger.log_thought_process(f"正在调用LLM API（第{attempt + 1}次尝试）...")
                
                response = requests.post(
                    self.llm_config.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.llm_config.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                if self.logger:
                    self.logger.log_thought_process(f"LLM API调用成功，返回结果")
                
                return result
                
            except requests.exceptions.RequestException as e:
                if attempt < self.llm_config.retry_attempts - 1:
                    if self.logger:
                        self.logger.log_thought_process(f"LLM API调用失败，{self.llm_config.retry_delay}秒后重试...")
                    time.sleep(self.llm_config.retry_delay)
                else:
                    if self.logger:
                        self.logger.log_thought_process(f"LLM API调用失败：{str(e)}")
                    raise
                    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """
        调用LLM聊天完成API（流式输出）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            流式输出的文本片段
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_config.api_key}"
        }
        
        payload = {
            "model": self.llm_config.model_name,
            "messages": messages,
            "temperature": temperature or self.llm_config.temperature,
            "max_tokens": max_tokens or self.llm_config.max_tokens,
            "stream": True
        }
        
        # 重试机制
        for attempt in range(self.llm_config.retry_attempts):
            try:
                if self.logger:
                    self.logger.log_thought_process(f"正在调用LLM API流式输出（第{attempt + 1}次尝试）...")
                
                response = requests.post(
                    self.llm_config.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.llm_config.timeout,
                    stream=True
                )
                
                response.raise_for_status()
                
                if self.logger:
                    self.logger.log_thought_process(f"LLM API流式输出开始")
                
                # 处理流式响应
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if self.logger:
                            self.logger.log_thought_process(f"收到流式数据行: {line[:200]}")
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            # 跳过空数据行
                            if not data or not data.strip():
                                continue
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        # 调用流式回调
                                        if self.stream_callback:
                                            self.stream_callback(content)
                                        yield content
                            except json.JSONDecodeError as e:
                                # 跳过无法解析的行，但记录调试信息
                                if self.logger:
                                    self.logger.log_thought_process(f"JSON解析错误: {e}, 数据: {data[:100]}")
                                continue
                                
                return
                
            except requests.exceptions.RequestException as e:
                if attempt < self.llm_config.retry_attempts - 1:
                    if self.logger:
                        self.logger.log_thought_process(f"LLM API流式输出失败，{self.llm_config.retry_delay}秒后重试...")
                    time.sleep(self.llm_config.retry_delay)
                else:
                    if self.logger:
                        self.logger.log_thought_process(f"LLM API流式输出失败：{str(e)}")
                    raise
                    
    def get_completion(self, prompt: str, **kwargs) -> str:
        """
        获取单次完成结果
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            完成结果文本
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        result = self.chat_completion(messages, **kwargs)
        
        # 提取响应内容
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise ValueError("Invalid API response format")
            
    def analyze_question(self, user_question: str, context: Optional[str] = None) -> str:
        """
        分析数据库问题
        
        Args:
            user_question: 用户问题
            context: 数据库上下文
            
        Returns:
            分析结果
        """
        prompt = QUESTION_ANALYSIS_PROMPT.format(
            user_question=user_question,
            context=context if context else "无"
        )
        
        return self.get_completion(prompt)
        
    def generate_sql(self, user_question: str, table_schema: Optional[str] = None) -> str:
        """
        生成SQL查询
        
        Args:
            user_question: 用户需求
            table_schema: 表结构信息
            
        Returns:
            SQL查询和说明
        """
        prompt = SQL_GENERATION_PROMPT.format(
            user_question=user_question,
            table_schema=table_schema if table_schema else "无"
        )
        
        return self.get_completion(prompt)
        
    def optimize_performance(self, sql_query: str, table_schema: Optional[str] = None, execution_plan: Optional[str] = None) -> str:
        """
        优化SQL性能
        
        Args:
            sql_query: 原始SQL查询
            table_schema: 表结构信息
            execution_plan: 执行计划
            
        Returns:
            优化建议
        """
        prompt = PERFORMANCE_OPTIMIZATION_PROMPT.format(
            sql_query=sql_query,
            table_schema=table_schema if table_schema else "无",
            execution_plan=execution_plan if execution_plan else "无"
        )
        
        return self.get_completion(prompt)
        
    def design_database(self, user_question: str, existing_schema: Optional[str] = None) -> str:
        """
        设计数据库表结构
        
        Args:
            user_question: 业务需求
            existing_schema: 现有表结构
            
        Returns:
            数据库设计建议
        """
        prompt = DATABASE_DESIGN_PROMPT.format(
            user_question=user_question,
            existing_schema=existing_schema if existing_schema else "无"
        )
        
        return self.get_completion(prompt)
        
    def troubleshoot(self, user_question: str, error_message: Optional[str] = None, sql_query: Optional[str] = None) -> str:
        """
        排查数据库问题
        
        Args:
            user_question: 问题描述
            error_message: 错误信息
            sql_query: 相关SQL
            
        Returns:
            排查建议
        """
        prompt = TROUBLESHOOTING_PROMPT.format(
            user_question=user_question,
            error_message=error_message if error_message else "无",
            sql_query=sql_query if sql_query else "无"
        )
        
        return self.get_completion(prompt)