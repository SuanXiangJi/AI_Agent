from openai import OpenAI
from dotenv import load_dotenv
import os
from config_loader import get_config_value,load_append_config

# 加载 .env 文件
load_dotenv()

def call_deepseek_api(messages,limit_temperature=0.1,limit_max_tokens=1000):
    print("正在调用 DeepSeek API...")
    # 从环境变量中获取 API Key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未在 .env 文件中设置")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                *messages
            ],
            stream=False,
            temperature=limit_temperature,  # 调整随机参数，范围 0-2，值越大越随机————默认不随机0.1
            max_tokens=limit_max_tokens    # 调整最大生成的 token 数量
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API 调用出错: {e}")
        return None
    
def get_api_response(messages): 
    """"直接使用api的回复"""
    response = call_deepseek_api(messages,limit_temperature=0.9,limit_max_tokens=1000)
    return response

def get_perfect_command(messages): 
    """生成一条合适的browser-use命令"""
    
    # 读取配置并拼接
    append_rules = load_append_config() 
    print(0)
    last_user_message = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
    if not last_user_message:
        return None
    print(1)
    fixed_cmd = {
        "role": "system", 
        "content": f"针对上下文并聚焦刚刚我的提问：“{last_user_message['content']}”，生成一份可以清晰描述我的操作要求的网页操作指南({append_rules})（告诉浏览器如何做即可，不需要回答我问题的结果）"
    }
    updated_messages = messages + [fixed_cmd]
    response = call_deepseek_api(updated_messages,limit_temperature=0.4,limit_max_tokens=100) 
    print(2)
    return response

def evaluate_conversation(messages):
    """评估对话是否适合作为browser-use命令"""
    # 提取上一条用户提问内容
    last_user_message = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
    if not last_user_message:
        return (0, None)
    
    evaluation_prompt = {
        "role": "system", 
        "content": f"针对上一条用户提问以及上下文：“{last_user_message['content']}”，评估其是否可以直接作为一个简单的browser-use命令？可以就回复“1”，否则回复“0”（回复单个数字即可）"
    }
    
    # 添加评估指令到消息末尾
    updated_messages = messages + [evaluation_prompt]
    print("原对话:",updated_messages)
    
    # 调用API
    response = call_deepseek_api(updated_messages,limit_temperature=0.1,limit_max_tokens=10)
    print("API响应:",response)
    
    # 解析响应
    if not response:
        return (0, None)
        
    first_line = response.split('\n')[0].strip()
    if first_line == '0':
        res_msg = get_api_response(messages)
        return (0, res_msg)
    elif first_line == '1':
        res_cmd = get_perfect_command(messages)
        return (1, res_cmd)
    else:# 如果API返回了其他内容，重新调用API
        i=0
        judge_num = get_config_value("re_judge")
        while i<judge_num:
            i+=1
            re_evaluation_prompt = {
                    "role": "system", 
                    "content": f"（直接回答数字！！！！）针对上一条用户提问以及上下文：“{last_user_message['content']}”，评估其是否可以直接作为一个简单的browser-use命令？可以的话或者当用户明确要求访问网站就回复“1”，否则回复“0”（直接回答数字！！！！）（直接回答数字！！！！）"
                } 
            re_updated_messages = messages + [re_evaluation_prompt] 
            temp = i/4
            response = call_deepseek_api(re_updated_messages,limit_temperature=temp,limit_max_tokens=10) 
            re_first_line = response.split('\n')[0].strip() 
            if re_first_line == '0':
                res_msg = get_api_response(messages)
                return (0, res_msg)
            elif re_first_line == '1':
                res_cmd = get_perfect_command(messages)
                return (1, res_cmd)
        return (0, "服务器繁忙，请稍后再试")
            

def generate_conversation_title(messages: list) -> str:
    """生成简短对话标题（不超过14字符）"""
    title_prompt = {
        "role": "system",
        "content": "请根据对话内容生成中文标题，必须极度简短，标点符号省略，最长不得超过14个字符，只返回标题内容不要任何格式"
    }
    
    try:
        response = call_deepseek_api(messages + [title_prompt])
        # 提取首行有效内容并截断
        clean_title = response.split('\n')[0].strip()[:14]
        return clean_title if clean_title else "未命名对话"
    except Exception as e:
        print(f"标题生成异常: {str(e)}")
        return "未命名对话"

# main测试函数
def main():
    messages = [
        {"role": "user", "content": "你好，DeepSeek!"},
        {"role": "assistant", "content": "你好！有什么我可以帮助你的吗？"},
        {"role": "user", "content": "你能告诉我今天的天气吗？"}
    ]
    
    status, msg = evaluate_conversation(messages)
    print(f"评估结果: {status}")
    if status == 0:
        print(f"完整响应: {msg}")



if __name__ == "__main__":
    main()

    