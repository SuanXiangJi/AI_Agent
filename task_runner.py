import streamlit as st
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import os
from pydantic import SecretStr
import platform
from log_handler import log_management
from datetime import datetime

load_dotenv()  # 加载环境变量

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import pathlib
save_path = pathlib.Path("logs/conversation")
save_path.mkdir(parents=True, exist_ok=True)

async def run_agent(task, log_container):
    api_key_deepseek = os.getenv('DEEPSEEK_API_KEY')
    if not api_key_deepseek:
        raise ValueError("未检测到DEEPSEEK_API_KEY，请检查.env文件配置")

    with log_management(log_container) as handler:
        llm = ChatOpenAI(
            base_url='https://api.deepseek.com/v1',
            model='deepseek-chat',
            api_key=SecretStr(api_key_deepseek)
        )

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        gif_path = f'./screenshots/screenshot_{current_time}.gif'

        agent = Agent(
            task=task,
            llm=llm,
            use_vision=False,
            generate_gif=gif_path,
            save_conversation_path=str(save_path), 
        )
        try:
            await agent.run()
            # 从会话状态日志中检测结果
            while True:
                if any("Result:" in log for log in st.session_state.get('execution_logs', [])):
                    result_log = next(log for log in reversed(st.session_state.execution_logs) if "Result:" in log)
                    result = result_log.split("Result:")[1].split("INFO     [agent]")[0].strip()
                    break
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            st.warning("任务已终止")
            result = "任务中断"

    return {
    "result": result or "任务完成",
    "gif_path": gif_path  # 返回生成的 GIF 路径
    }

async def run_task(task, log_container):
    st.session_state.agent_result = await run_agent(task, log_container)