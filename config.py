# 想换个模型，只要改 config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 统一管理配置项
MODEL_API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
MODEL_NAME = "qwen3-max-2026-01-23"
VECTOR_SEARCH_K = 5  # 检索返回的文档数量
EMBEDDING_MODEL = "text-embedding-v3"  # 升级为 V3