# core.py (Day 7 终极修正版)
import os
import logging
from typing import List, Generator

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
# from langchain_core.runnables import RunnablePassthrough
# from openai import APIConnectionError, RateLimitError 

# 确保 config.py 和 prompts.py 存在
from config import MODEL_API_KEY, MODEL_BASE_URL, MODEL_NAME, VECTOR_SEARCH_K
from prompts import get_rag_prompt

logger = logging.getLogger(__name__)

# --- 1. 加载函数 (保留了 chunk_size=1000 的优化) ---
def load_and_split_document(file_path: str) -> List[Document]:
    logger.info(f"正在加载文档: {file_path}")
    from langchain_community.document_loaders import (
        PyMuPDFLoader, 
        TextLoader, 
        Docx2txtLoader,
        UnstructuredMarkdownLoader
    )
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    # 1. 获取文件扩展名 (例如 .pdf, .txt)
    ext = os.path.splitext(file_path)[1].lower()
    
    # 2. 工厂模式：根据后缀选择加载器
    if ext == ".pdf":
        loader = PyMuPDFLoader(file_path)
    elif ext == ".txt":
        # encoding="utf-8" 很重要，防止中文乱码
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        # 遇到不支持的格式，抛出异常或者返回空
        raise ValueError(f"不支持的文件格式: {ext}")
    
    # 3. 加载文档
    pages = loader.load_and_split()
    
    # 4. 切分文档 (保持 Day 7 的 1000/300 配置)
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=300, 
        length_function=len, 
        add_start_index=True,
    )
    texts = text_splitter.create_documents([page.page_content for page in pages])
    logger.info(f"文档切分完成，共 {len(texts)} 个片段")
    return texts

# --- 2. 建库函数 ---
def build_vector_store(documents: List[Document]) -> FAISS:
    logger.info("正在构建向量数据库...")
    from langchain_community.embeddings.dashscope import DashScopeEmbeddings
    import os
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v3", 
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    db = FAISS.from_documents(documents, embeddings)
    logger.info("向量数据库构建完毕")
    return db

# --- 3. 内部流水线组装 (这里修复了报错的核心) ---
def _get_rag_chain(vector_store: FAISS, prompt_template: str):
    retriever = vector_store.as_retriever(search_kwargs={"k": VECTOR_SEARCH_K})
    
    llm = ChatOpenAI(
        temperature=0.3, # 稍微调高一点点，让幽默人设能发挥
        base_url=MODEL_BASE_URL,
        api_key=MODEL_API_KEY,
        model=MODEL_NAME,
    )
    
    # 🌟 核心修改：使用传入的模板文本
    prompt = get_rag_prompt(prompt_template)
    
    rag_chain = (
        {
            "context": itemgetter("question") | retriever, 
            "question": itemgetter("question"),
            "chat_history": itemgetter("chat_history"),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

# --- 4. 同步生成 (CLI 用) ---
def generate_rag_response(query: str, vector_store: FAISS) -> str:
    logger.info("正在调用 API (同步)...")
    try:
        chain = _get_rag_chain(vector_store)
        return chain.invoke(query)
    except Exception as e:
        logger.error(f"调用失败: {e}")
        return f"出错了: {e}"

# --- 5. 流式生成 (Web 用) ---
def stream_rag_response(query: str, vector_store: FAISS, chat_history: List[dict], prompt_template: str) -> Generator[str, None, None]:
    logger.info("正在调用 API (流式)...")
    try:
        # 把 template 传给内部函数
        chain = _get_rag_chain(vector_store, prompt_template)
        
        for chunk in chain.stream({
            "question": query,
            "chat_history": chat_history
        }):
            yield chunk
    except Exception as e:
        logger.error(f"流式失败: {e}")
        yield f"出错了: {e}"