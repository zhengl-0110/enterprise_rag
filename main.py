import os
from dotenv import load_dotenv

# 这行代码会自动寻找并加载 .env 文件中的变量
load_dotenv()

# 安全读取，如果没读到会返回 None，而不是报错（后续我们会学怎么处理 None）
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("✅ 成功读取 API Key (安全模式)")
    # 这里只是演示，实际不要打印 key 的内容！
    print(f"Key 的前几位: {api_key[:5]}...")
else:
    print("❌ 未找到 API Key，请检查 .env 文件")