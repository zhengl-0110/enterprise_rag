import streamlit as st
import os
from core import load_and_split_document, build_vector_store, stream_rag_response
from langchain_core.messages import AIMessage, HumanMessage

# 设置页面标题
st.set_page_config(page_title="小雷的 AI 知识库助手", page_icon="🤖")
st.title("🤖 小雷的 AI 智能问答助手")

# --- 侧边栏：文件上传区 ---
with st.sidebar:
    st.header("📄 文档上传")
    # 🌟 修改这里：增加 txt, docx, md 支持
    uploaded_file = st.file_uploader(
        "请上传文件 (支持 PDF, Word, TXT, MD)", 
        type=["pdf", "txt", "docx", "md"]
    )
    # 增加一个重置按钮
    if st.button("清除历史"):
        # 清除所有缓存
        for key in ["vector_store", "current_file"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# --- 主逻辑区 ---
if uploaded_file:
    # 🛠️ 优化 1：确保 data 目录存在，防止报错
    os.makedirs("data", exist_ok=True)
    
    file_path = os.path.join("data", uploaded_file.name)
    
    # 保存文件
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.toast(f"文件已保存: {uploaded_file.name}", icon="✅")

    # 🛠️ 优化 2：检测是否换了新文件
    # 如果当前没有库，或者上传的文件名和内存里的不一样，就重新构建
    is_new_file = "current_file" not in st.session_state or st.session_state["current_file"] != uploaded_file.name
    
    if is_new_file:
        with st.spinner(f"正在学习新文档: {uploaded_file.name} ..."):
            try:
                # 重新构建
                docs = load_and_split_document(file_path)
                vector_store = build_vector_store(docs)
                
                # 更新 session_state
                st.session_state["vector_store"] = vector_store
                st.session_state["current_file"] = uploaded_file.name # 👈 记住当前文件名
                
                st.success(f"✅ 新知识库构建完成！包含 {len(docs)} 个片段。")
            except Exception as e:
                st.error(f"构建失败: {e}")
    
    # 提示当前正在使用的文件
    elif "vector_store" in st.session_state:
        st.info(f"🧠 当前知识库: {st.session_state['current_file']} (已就绪)")

    st.divider()

    # 3. 问答交互区 (保持不变)
    # 初始化对话历史 (如果不存在的话)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🌟 关键：每次刷新页面，都要把历史聊天记录重新画出来
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 处理用户输入
    prompt = st.chat_input("在这个文档里找什么？")
    
    if prompt:
        # 1. 显示用户提问
        with st.chat_message("user"):
            st.markdown(prompt)
        # 记入历史
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. 准备传给后端的 history
        # 将 session_state 里的简单字典转换为 LangChain 的 Message 对象
        chat_history = []
        for msg in st.session_state.messages[:-1]: # 不包含当前这一句最新的
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))

        # 3. 生成回答
        if "vector_store" in st.session_state:
            with st.chat_message("assistant"):
                # 🌟 传入 chat_history
                response = st.write_stream(
                    stream_rag_response(
                        prompt, 
                        st.session_state["vector_store"], 
                        chat_history
                    )
                )
            # 记入历史
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.error("请先等待知识库构建完成。")

else:
    st.info("👈 请先在左侧上传一个 PDF 文档开始体验。")