# 想优化回答效果，只要改 prompts.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 🌟 新增：多轮对话的 System Prompt
# 我们显式地加了一个 {chat_history} 的占位符
RAG_SYSTEM_TEMPLATE = """You are a helpful assistant. 
Answer the question based only on the following context. 
If the context is in English but the question is in Chinese, please translate the relevant information and answer in Chinese.

Context:
{context}
"""

def get_rag_prompt() -> ChatPromptTemplate:
    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_TEMPLATE),
        # 🌟 关键点：这里是放历史记录的地方
        # 它可以是一长串的 HumanMessage, AIMessage 对象
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    return prompt