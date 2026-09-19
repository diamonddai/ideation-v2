import logging
import logging.handlers
import os
from datetime import datetime

def setup_advanced_logging(log_level="DEBUG", log_dir="logs"):
    """
    设置高级日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日志文件目录
    """
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    detailed_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器 - 只显示应用相关日志
    console_handler = logging.StreamHandler()
    console_level = getattr(logging, log_level.upper())
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(lambda record: not any(
        name in record.name for name in [
            'httpx', 'openai', 'httpcore', 'python_multipart', 
            'uvicorn.access', 'watchfiles', 'urllib3'
        ]
    ))
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 所有日志
    all_log_file = os.path.join(log_dir, "app.log")
    file_handler = logging.handlers.RotatingFileHandler(
        all_log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(detailed_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志文件
    error_log_file = os.path.join(log_dir, "error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(detailed_format)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别 - 过滤噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("openai._base_client").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.proxy").setLevel(logging.WARNING)
    logging.getLogger("python_multipart").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
    
    # 确保所有子日志器继承根日志器的级别
    # 设置propagate=True，让子日志器将消息传播到父日志器
    for logger_name in [
        "agents",
        "agents.module1_data_understanding", 
        "agents.module1_data_understanding.data_pattern_agent",
        "agents.module1_data_understanding.context_analysis_agent",
        "agents.module1_data_understanding.module1_controller"
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = True  # 确保消息传播到根日志器
    
    # 创建应用日志器
    app_logger = logging.getLogger("metaphor_backend")
    app_logger.info(f"🚀 日志系统初始化完成，级别: {log_level}")
    
    return app_logger

def get_logger(name):
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    return logging.getLogger(name)

# 日志级别颜色映射
LOG_COLORS = {
    'DEBUG': '\033[36m',    # 青色
    'INFO': '\033[32m',     # 绿色
    'WARNING': '\033[33m',  # 黄色
    'ERROR': '\033[31m',    # 红色
    'CRITICAL': '\033[35m', # 紫色
    'RESET': '\033[0m'      # 重置
}

class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    def format(self, record):
        # 添加颜色
        if record.levelname in LOG_COLORS:
            record.levelname = f"{LOG_COLORS[record.levelname]}{record.levelname}{LOG_COLORS['RESET']}"
        
        return super().format(record) 