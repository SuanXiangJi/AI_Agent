import streamlit as st
import logging
import contextlib

class StreamlitLogHandler(logging.Handler):
    def __init__(self, log_container):
        super().__init__()
        self.log_display = log_container  # 直接使用传入的容器
        self.setFormatter(logging.Formatter('%(asctime)s - %(message)s', "%H:%M:%S"))

    def emit(self, record):
        log_entry = self.format(record)
        if 'execution_logs' not in st.session_state:
            st.session_state.execution_logs = []

        st.session_state.execution_logs.append(log_entry)

        # 新增折叠控制组件
        with self.log_display:
            with st.expander("🤖 任务日志（点击展开/折叠）", expanded=True):
                st.markdown(f'''
                <div style="
                    max-height: 1200px;
                    overflow-y: auto;
                    font-size: 13px;
                    line-height: 1.4;
                    padding: 8px;
                    background: black;
                    border-radius: 4px;
                    color: #FFFFE0;
                    border: 1px solid #FFFFE0;
                ">
                {"<br>".join(st.session_state.execution_logs)}
                </div>
                ''', unsafe_allow_html=True)

@contextlib.contextmanager
def log_management(log_container):
    """
    日志管理上下文管理器。用于在 Streamlit 应用中临时添加和移除日志处理器。

    参数:
        log_container: Streamlit 容器对象,用于显示日志输出

    上下文管理器会:
    1. 为 browser_use 和 root logger 添加 StreamlitLogHandler
    2. 设置日志级别为 INFO
    3. 退出时自动移除添加的处理器

    用法示例:
        with log_management(st.container()):
            # 日志会输出到指定的 Streamlit 容器
            logger.info("这是一条日志")
    """
    handler = StreamlitLogHandler(log_container)
    browser_use_logger = logging.getLogger('browser_use')
    root_logger = logging.getLogger()

    try:
        browser_use_logger.addHandler(handler)
        root_logger.addHandler(handler)
        browser_use_logger.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
        yield handler
    finally:
        browser_use_logger.removeHandler(handler)
        root_logger.removeHandler(handler)