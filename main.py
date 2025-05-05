import streamlit as st
from config_loader import load_append_config, load_inner_web_scale
from task_runner import run_task
from auth import register, login, is_logged_in, logout
from deepseek_api import evaluate_conversation, generate_conversation_title
import asyncio
import re
import requests
import streamlit.components.v1 as components
from database import User, Task, Conversation

# 基本页面配置
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
) 

# 添加自定义 CSS 样式
def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("css/main_styles.css")

# 添加自定义 CSS 来设置任务按钮宽度为最大
st.markdown("""
<style>
.task-button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'task_running' not in st.session_state:
    st.session_state.task_running = False
if 'agent_result' not in st.session_state:
    st.session_state.agent_result = None
if 'current_task' not in st.session_state:
    st.session_state.current_task = None
if 'show_confirm' not in st.session_state:
    st.session_state.show_confirm = False
    st.session_state.task_to_delete = None
    st.session_state.task_name_to_delete = None
if 'first_question' not in st.session_state:
    st.session_state.first_question = True

# 检查用户是否已登录
if is_logged_in():
    user = User.get_user_by_id(st.session_state.user_id)

    # 侧边栏
    with st.sidebar:
        # 将退出登录和创建对话按钮放在同一行分成两列显示
        col1, col2 = st.columns(2)
        with col1:
            st.button("退出登录", on_click=logout, key="logout_button")
        with col2:
            if st.button("新建对话"):
                new_task = Task.create_task(user.id, "New Task")
                st.session_state.current_task = new_task.task_id
                st.session_state.first_question = True

        # 画一条直线区分开来
        st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)

        # 处理确认删除，放在历史对话标题上面
        if st.session_state.show_confirm:
            st.warning(f"确定要删除任务对话 '{st.session_state.task_name_to_delete}' 吗？")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("确认", key=f"confirm_delete_{st.session_state.task_to_delete}"):
                    Task.mark_task_as_deleted(st.session_state.task_to_delete)
                    # 重置确认状态
                    st.session_state.show_confirm = False
                    st.session_state.task_to_delete = None
                    st.session_state.task_name_to_delete = None
                    # 刷新页面
                    st.rerun()
            with col4:
                if st.button("取消", key=f"cancel_delete_{st.session_state.task_to_delete}"):
                    # 重置确认状态
                    st.session_state.show_confirm = False
                    st.session_state.task_to_delete = None
                    st.session_state.task_name_to_delete = None
                    # 立即刷新页面
                    st.rerun()
            # 在确认和取消按钮下面添加横线
            st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)

        # 任务列表标题
        st.markdown("<h4 style='text-align: left;'>历史对话</h4>", unsafe_allow_html=True)

        # 获取所有任务并按 updated_at 排序
        tasks = Task.get_tasks_by_user_id(user.id, is_deleted=0)
        sorted_tasks = sorted(tasks, key=lambda x: x.updated_at, reverse=True)

        # 显示任务列表
        for task in sorted_tasks:
            col1, col2 = st.columns([5, 1])
            with col1:
                # 使用 st.button 并添加自定义 CSS 类
                if st.button(task.task_name, key=f"task_button_{task.task_id}", help=None, type="secondary", disabled=False, use_container_width=True):
                    st.session_state.current_task = task.task_id
            with col2:
                if st.button("X", key=f"delete_button_{task.task_id}"):
                    st.session_state.show_confirm = True
                    st.session_state.task_to_delete = task.task_id
                    st.session_state.task_name_to_delete = task.task_name
                    # 强制刷新页面
                    st.rerun()

    st.title("AI Chatbot")

    prompt = st.chat_input("请输入任务", disabled=st.session_state.task_running)
    log_container = st.container()

    # 如果当前任务为空，等待用户输入后创建新任务
    if st.session_state.current_task is None and prompt:
        new_task = Task.create_task(user.id, "New Task")
        st.session_state.current_task = new_task.task_id

    # 从数据库获取当前任务的对话历史
    if st.session_state.current_task is not None:
        conversations = Conversation.get_conversations_by_task_id(st.session_state.current_task)
        scale = load_inner_web_scale()
        for conv in conversations:
            role = "ai" if conv.is_ai else "human"
            with st.chat_message(role):
                st.write(conv.result)
                if role == "ai":
                    st.markdown("<hr style='border: 1px solid #cfc;'>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                if role == "ai" and conv.gif:
                    with col1:
                        st.write("\n操作过程动画：")
                        st.image(conv.gif, caption="", use_container_width=True)
                        st.markdown(
                            f"""
                            <style>
                            [data-testid="stImage"] img {{
                                max-height: 810px;
                                width: auto;
                                padding-top: 30px;
                            }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                if role == "ai" and conv.links:
                    links = conv.links.split('   ')
                    links = [link.strip() for link in links if link.strip()]
                    if links:
                        with col2:
                            if len(links) > 0:
                                selected_link = st.selectbox("选择要显示的链接", links, index=0, key=f"selectbox_{conv.conversation_id}")
                            html = f"""
                            <div style="transform: scale({scale}); transform-origin: 0 0;">
                                <iframe src="{selected_link}" width="{1/scale * 100}%" height="{1/scale * 710}" scrolling="yes" frameborder="0" style="border-radius: 8px; border: 1px solid #e0e0e0;"></iframe>
                            </div>
                            """
                            if len(links) > 1:
                                st.write("")  # 用于分隔选项和网页
                            components.html(html, height=720, scrolling=False) 

    if prompt and not st.session_state.task_running:
        # 整合历史对话记录
        chat_history = []
        if st.session_state.current_task is not None:
            conversations = Conversation.get_conversations_by_task_id(st.session_state.current_task)
            for conv in conversations:
                role = "user" if conv.is_ai == 0 else "assistant"
                chat_history.append({"role": role, "content": conv.result})

        

        # 添加当前提问到历史对话中
        chat_history.append({"role": "user", "content": prompt})

        # 原始输入
        with st.chat_message("human"):
            st.write(prompt)
            if st.session_state.current_task is not None:
                Conversation.create_conversation(st.session_state.current_task, user.id, prompt, 0)
        

        # 如果是第一次提问，生成标题并更新任务标题
        if st.session_state.first_question:
            title = generate_conversation_title(chat_history)
            if title:
                Task.update_task_title(st.session_state.current_task, title)
            st.session_state.first_question = False

   
 
 

        # 请求deepseek api的评估方法
        status, msg = evaluate_conversation(chat_history)
 

        if status == 0: 
            # ai_message = st.chat_message("ai")
            result = msg
            with st.chat_message("ai"):
                st.write(result)
            if st.session_state.current_task is not None:
                Conversation.create_conversation(st.session_state.current_task, user.id, result, 1)

        elif status == 1:
            ai_message = st.chat_message("ai")
            log_container = ai_message.empty()

            with log_container:
                st.session_state.task_running = True
                try:
                    asyncio.run(run_task(msg, log_container))
                except Exception as e:
                    st.error(f"执行错误: {str(e)}")
                    st.session_state.task_running = False
                finally:
                    st.session_state.task_running = False

            if st.session_state.agent_result:
                result = st.session_state.agent_result["result"]
                gif_path = st.session_state.agent_result["gif_path"]
                result_text = st.session_state.agent_result["result"]
                # 使用正则表达式提取所有的 HTTP/HTTPS 链接
                links = re.findall(r'https?://[^\s]+', result_text)
                # 处理链接，去除末尾的右括号或句号
                clean_links = []
                for link in links:
                    if link.endswith((')', '。', ',', '）', ']')):
                        link = link[:-1]
                    clean_links.append(link)
                # 三空格区分链接
                links_text = '   '.join(clean_links)

                with st.chat_message("ai"):
                    st.write(result)
                    st.markdown("<hr style='border: 1px solid #cfc;'>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    if gif_path:
                        with col1:
                            st.write("\n操作过程动画：")
                            st.image(gif_path, caption=" ", use_container_width=True)
                            st.markdown(
                                f"""
                                <style>
                                [data-testid="stImage"] img {{
                                    max-height: 810px;
                                    width: auto;
                                    padding-top: 30px;
                                }}
                                </style>
                                """,
                                unsafe_allow_html=True
                            )
                    if clean_links:
                        with col2:
                            if len(clean_links) > 0:
                                selected_link = st.selectbox("选择要显示的链接", clean_links, index=0, key=f"selectbox_new_{st.session_state.current_task}")
                            html = f"""
                            <div style="transform: scale({scale}); transform-origin: 0 0;">
                                <iframe src="{selected_link}" width="{1/scale * 100}%" height="{1/scale * 710}" scrolling="yes" frameborder="0" style="border-radius: 8px; border: 1px solid #e0e0;"></iframe>
                            </div>
                            """
                            if len(clean_links) > 1:
                                st.write(" ")  # 用于分隔选项和网页
                            components.html(html, height=720, scrolling=False)
                    if st.session_state.current_task is not None:
                        Conversation.create_conversation(st.session_state.current_task, user.id, result, 1, gif=gif_path, links=links_text)

else:
    st.markdown("<div class='auth-wrapper'><text><h4>请先登录</h4></text>", unsafe_allow_html=True)
    auth_type = st.radio("", ["🔐 登录", "📝 注册"], horizontal=True)
    if auth_type == "📝 注册":
        register()  # 直接调用自带表单的函数
    else:
        login()     # 直接调用自带表单的函数
    st.markdown("</div>", unsafe_allow_html=True)
    