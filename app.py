import streamlit as st
import os
# 复用我们之前写好的核心逻辑
from core import load_and_split_document, build_vector_store, generate_rag_response

# 设置页面标题
st.set_page_config(page_title="我的 AI 知识库助手", page_icon="🤖")
st.title("🤖 小雷的 AI 智能问答助手")

# --- 侧边栏：文件上传区 ---
with st.sidebar:
    st.header("📄 文档上传")
    uploaded_file = st.file_uploader("请上传 PDF 文件", type=["pdf"])
    
    # 增加一个重置按钮
    if st.button("清除历史"):
        if "vector_store" in st.session_state:
            del st.session_state["vector_store"]
        st.rerun()

# --- 主逻辑区 ---
if uploaded_file:
    # 1. 处理文件：Streamlit 上传的是内存对象，我们需要把它存到硬盘上才能让 PyMuPDFLoader 读取
    file_path = os.path.join("data", uploaded_file.name)
    
    # 只有当文件还没保存过，或者换了新文件时才写入
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.toast(f"文件已保存: {uploaded_file.name}", icon="✅")

    # 2. 构建知识库 (关键点：使用 session_state 避免重复计算)
    # 只有当 session_state 里没有 vector_store 时，才去执行耗时的构建过程
    if "vector_store" not in st.session_state:
        with st.spinner("正在阅读文档并构建知识库... (这可能需要一点时间)"):
            try:
                docs = load_and_split_document(file_path)
                vector_store = build_vector_store(docs)
                # 把构建好的库“存”进浏览器的缓存里
                st.session_state["vector_store"] = vector_store
                st.success(f"✅ 知识库构建完成！包含 {len(docs)} 个文档切片。")
            except Exception as e:
                st.error(f"构建失败: {e}")
    else:
        st.info("🧠 知识库已就绪，可以直接提问。")

    st.divider() # 画一条分割线

    # 3. 问答交互区
    # 创建一个聊天输入框
    prompt = st.chat_input("在这个文档里找什么？")
    
    if prompt:
        # 显示用户的提问
        with st.chat_message("user"):
            st.write(prompt)

        # 显示 AI 的回答
        if "vector_store" in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("AI 正在思考..."):
                    # 调用我们 Day 2 写的核心函数
                    response = generate_rag_response(prompt, st.session_state["vector_store"])
                    st.write(response)
        else:
            st.error("请先等待知识库构建完成。")

else:
    st.info("👈 请先在左侧上传一个 PDF 文档开始体验。")