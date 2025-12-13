import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # API配置
    API_PREFIX = '/api/v1'

    # 转换配置
    MAX_INPUT_LENGTH = 1000
    DEFAULT_OUTPUT_FORMAT = 'latex'
    SUPPORTED_FORMATS = ['latex', 'mathml', 'asciimath']

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass


config = Config()