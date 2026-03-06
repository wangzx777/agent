import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    配置管理器 - 支持多级配置加载
    
    配置加载优先级（从高到低）：
    1. 环境变量
    2. 用户指定的配置文件路径
    3. src/config/config.yaml（推荐位置）
    4. 项目根目录下的 llm_config.yaml（向后兼容）
    5. 默认值
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 可选的配置文件路径。如果未指定，将按优先级顺序查找配置文件
        """
        self.config_path = self._find_config_path(config_path)
        self.config = self._load_config()
    
    def _find_config_path(self, config_path: Optional[str] = None) -> Path:
        """查找配置文件路径，按优先级顺序"""
        if config_path:
            return Path(config_path)
        
        # 优先级 1: src/config/config.yaml（推荐位置）
        src_config = Path("src/config/config.yaml")
        if src_config.exists():
            return src_config
        
        # 优先级 2: 项目根目录的 llm_config.yaml（向后兼容）
        root_config = Path("llm_config.yaml")
        if root_config.exists():
            return root_config
        
        # 如果都没有找到，使用默认路径（会在加载时抛出异常）
        return Path("src/config/config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please create a config file or copy the template:\n"
                f"cp src/config/config.template.yaml src/config/config.yaml"
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_llm_config(self) -> "LLMConfig":
        """获取 LLM 配置"""
        # 支持新旧两种配置格式
        if "llm" in self.config:
            # 新格式：config.llm
            return LLMConfig(**self.config["llm"])
        else:
            # 旧格式：直接在根级别，但需要过滤掉非LLM相关的字段
            llm_fields = {
                'api_url', 'api_key', 'model_name', 'temperature', 
                'max_tokens', 'timeout', 'retry_attempts', 'retry_delay', 'stream'
            }
            llm_config_dict = {
                k: v for k, v in self.config.items() 
                if k in llm_fields
            }
            return LLMConfig(**llm_config_dict)
    
    def get_mcp_url(self) -> str:
        """获取MCP服务URL，优先从环境变量读取，其次从配置文件，最后使用默认值"""
        # 1. 首先检查环境变量
        mcp_url_env = os.getenv("MCP_URL")
        if mcp_url_env:
            return mcp_url_env
        
        # 2. 检查配置文件中的mcp配置（支持新旧格式）
        if "mcp" in self.config:
            # 新格式：config.mcp.url
            mcp_config = self.config["mcp"]
        else:
            # 旧格式：直接在根级别找 mcp
            mcp_config = self.config.get("mcp", {})
        
        mcp_url_config = mcp_config.get("url")
        if mcp_url_config:
            return mcp_url_config
        
        # 3. 使用默认值
        return "http://192.168.180.37:8005/sse"
    
    def get_config_value(self, key_path: str, default=None):
        """
        获取配置值，支持嵌套键路径
        
        Args:
            key_path: 键路径，如 "llm.temperature" 或 "mcp.timeout"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default


class LLMConfig:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 20000,
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