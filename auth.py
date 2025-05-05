import streamlit as st
from database import User, Token
from werkzeug.security import check_password_hash, generate_password_hash
import extra_streamlit_components as stx
import jwt
import re
import platform
import os

# 初始化 CookieManager
cookie_manager = stx.CookieManager()
SECRET_KEY = os.getenv('SECRET_KEY')

def get_device_info():
    return platform.platform()
def register():
    st.title("用户注册")
    with st.form(key="register_form", clear_on_submit=True):
        nickname = st.text_input(label="昵称",  placeholder="您的昵称", help="随意选取一个您喜欢的昵称")
        email = st.text_input(label="邮箱地址",  placeholder="example@jiangnan.edu.cn" , help="用于登录和接收通知的有效邮箱")
        password = st.text_input( label="登录密码", type="password",placeholder="至少8位且包含两种字符组合" ) 
        
        if st.form_submit_button("立即注册"):
            if not is_password_complex(password):
                st.error('密码需至少8位，且包含数字、字母（大小写）或符号中的两种组合。')
                return
            existing_user = User.get_user_by_email(email)
            if existing_user:
                st.error('该邮箱已被注册')
                return
            try:
                hashed_password = generate_password_hash(password)
                new_user = User.create_user(nickname, email, hashed_password)
                if new_user:
                    st.success("注册成功，自动登录")
                    
                    device_info = get_device_info()
                    token = Token.create_token(new_user.id, device_info)
                    cookie_manager.set("token", token, domain='your_domain', path='/')
                    
                    st.session_state.user_id = new_user.id  
                    st.rerun()
                else:
                    st.error('注册失败，请重试')
            except Exception as e:
                st.error(f'系统错误: {str(e)}')

def login():
    st.title("用户登录")
    with st.form(key="login_form", clear_on_submit=False):  # 添加表单容器
        email = st.text_input(label="邮箱地址",  placeholder="example@jiangnan.edu.cn" , help="用于登录和接收通知的有效邮箱")
        password = st.text_input(label="登录密码", type="password",placeholder="至少8位且包含两种字符组合" )
        if st.form_submit_button("登录"): 
            user = User.get_user_by_email(email)
            if(user is None):
                st.error('该邮箱未注册')
            elif check_password_hash(user.password, password):
                st.success("登录成功")
                
                device_info = get_device_info()
                token = Token.create_token(user.id, device_info)
                cookie_manager.set("token", token, domain='your_domain', path='/')

                st.session_state.user_id = user.id
                st.rerun()
            else:
                st.error('邮箱或密码错误') 

def is_logged_in():
    # 从 cookie 中获取 token
    token = cookie_manager.get("token")
    device_info = get_device_info()
    # print(f"当前设备信息: {device_info}")
    # print(f"从 cookie 中获取的 token: {token}")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            # print(f"解码后的 user_id: {user_id}")
            is_valid = Token.is_token_valid(token, device_info)
            # print(f"token 是否有效: {is_valid}")
            if user_id and is_valid:
                st.session_state.user_id = user_id
                return True
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            print("token 无效")
            pass
    return False

def logout():
    # 删除 cookie 中的 token
    cookie_manager.delete("token")
    st.session_state.pop('user_id', None)
    st.session_state.pop('token', None)

def is_password_complex(password):
    if len(password) < 8:
        return False
    if password.isdigit():
        return False
    patterns = [r'[0-9]', r'[a-z]', r'[A-Z]', r'[!@#$%^&*(),.?":{}|<>]']
    match_count = 0
    for pattern in patterns:
        if re.search(pattern, password):
            match_count += 1
    return match_count >= 2