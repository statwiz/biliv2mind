import streamlit as st
import json
import time
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from coze_api import CozeAPI
from config import BOT_ID, COZE_API_TOKEN, API_URL, EXPECTED_PARAMS
from utils import truncate_text, get_current_time, parse_workflow_response, parse_bilibili_url
import streamlit.components.v1 as components

# 设置页面配置为亮色主题，取消wide模式
st.set_page_config(
    page_title="",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - B站风格
st.markdown("""
<style>
    /* B站风格配色 */
    :root {
        --bilibili-pink: #FB7299;
        --bilibili-blue: #23ADE5;
        --bilibili-light-blue: #B3D4FC;
        --bilibili-white: #FFFFFF;
        --bilibili-gray: #F1F2F3;
        --bilibili-text: #212121;
    }
    
    /* 修改整体背景色为白色 */
    .stApp {
        background-color: var(--bilibili-white);
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: var(--bilibili-text) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(to right, var(--bilibili-pink), #e45c84);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: background 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(to right, #e45c84, var(--bilibili-pink));
    }
    
    /* 信息框样式 */
    .stAlert {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 移除输入框容器的黑色背景和边框 */
    .stTextInput > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 移除输入框的黑色背景和边框 */
    .stTextInput > div > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 文本区域样式 */
    .stTextArea textarea {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 0.5rem;
    }
    
    /* 分隔线样式 */
    hr {
        border-top: 1px solid var(--bilibili-light-blue);
    }
    
    /* 标题栏样式 */
    .main-header {
        color: var(--bilibili-pink);
        text-align: center;
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
    }
    
    /* 卡片样式 */
    .content-card {
        background-color: var(--bilibili-gray);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 调整列宽度 */
    .equal-width-cols {
        display: flex;
    }
    .equal-width-cols > div {
        flex: 1;
        padding: 15px;
    }
    
    /* 其他文本颜色为黑色 */
    h1, h2, h3, p, div {
        color: var(--bilibili-text) !important;
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        background-color: var(--bilibili-white) !important;
        color: var(--bilibili-pink) !important;
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 0.5rem;
    }
    
    div.stButton > button {
        color: white !important;
        background-color: #FB7299 !important;
    }
    
    ::placeholder {
        color: gray !important;
        opacity: 1 !important; /* 确保颜色不透明 */
    }
</style>
""", unsafe_allow_html=True)

# 持久化存储目录
STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(exist_ok=True)
USAGE_FILE = STORAGE_DIR / "usage_data.pkl"

# 获取用户标识（IP地址或会话ID）
def get_user_identifier():
    # 获取客户端IP地址
    try:
        # 兼容不同版本的Streamlit
        client_ip = "unknown"
        if hasattr(st, "query_params"):
            try:
                client_ip = st.query_params.get("client_ip", ["unknown"])[0]
            except:
                pass
        elif hasattr(st, "experimental_get_query_params"):
            try:
                params = st.experimental_get_query_params()
                client_ip = params.get("client_ip", ["unknown"])[0]
            except:
                pass
    except:
        client_ip = "unknown"
    
    # 创建一个基于IP和日期的标识符
    # 这样每天都会重置限制，但同一天内同一IP的限制是持久的
    today = datetime.now().strftime("%Y-%m-%d")
    identifier = f"{client_ip}_{today}"
    
    # 使用哈希函数增加隐私保护
    return hashlib.md5(identifier.encode()).hexdigest()

# 加载使用数据
def load_usage_data():
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, "rb") as f:
                return pickle.load(f)
        except:
            return {}
    return {}

# 保存使用数据
def save_usage_data(data):
    with open(USAGE_FILE, "wb") as f:
        pickle.dump(data, f)

# 获取或初始化用户使用数据
def get_user_usage(user_id):
    usage_data = load_usage_data()
    if user_id not in usage_data:
        usage_data[user_id] = {
            "call_count": 0,
            "last_call_time": None,
            "call_history": {}
        }
        save_usage_data(usage_data)
    return usage_data[user_id]

# 更新用户使用数据
def update_user_usage(user_id, call_count=None, last_call_time=None, call_history=None):
    usage_data = load_usage_data()
    if user_id not in usage_data:
        usage_data[user_id] = {
            "call_count": 0,
            "last_call_time": None,
            "call_history": {}
        }
    
    if call_count is not None:
        usage_data[user_id]["call_count"] = call_count
    
    if last_call_time is not None:
        usage_data[user_id]["last_call_time"] = last_call_time
    
    if call_history is not None:
        usage_data[user_id]["call_history"] = call_history
    
    save_usage_data(usage_data)

# 获取用户标识符
user_id = get_user_identifier()
user_usage = get_user_usage(user_id)

# 初始化会话状态
if 'call_count' not in st.session_state:
    st.session_state.call_count = user_usage["call_count"]
if 'last_call_time' not in st.session_state:
    st.session_state.last_call_time = user_usage["last_call_time"]
if 'call_history' not in st.session_state:
    st.session_state.call_history = user_usage["call_history"]
if 'cache' not in st.session_state:
    st.session_state.cache = {}
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'result_data' not in st.session_state:
    st.session_state.result_data = None

# 调用限制配置
MAX_CALLS_PER_SESSION = 30  # 每个会话最大调用次数
WORKFLOW_TIMEOUT = 5 * 60  # 工作流执行超时时间（秒）
MAX_RETRY_COUNT = 3  # 最大重试次数

# 确保输入字段和按钮在主标题下正确对齐，标题使用Bilibili粉红色
#st.markdown('<div class="main-header"><h1 style="color: #FB7299 !important;">B站视频思维导图生成器</h1></div>', unsafe_allow_html=True)

components.html("""
    <h1 style=" 
        text-align: center;
        color: #FB7299; font-size: 36px;
    ">
        B站视频链接转思维导图
    </h1>
""", height=85)

# 添加副标题框
# st.markdown('<div style="background-color: #F1F2F3; border-radius: 10px; padding: 10px; text-align: center; color: #FB7299; font-size: 1.2rem;">主要用于知识分享类视频</div>', unsafe_allow_html=True)
components.html("""
    <div style="
        background-color: #F1F2F3;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        color: #FB7299;
        font-size: 1.2rem;
        font-weight: bold;
    ">
        主要用于知识分享类视频
    </div>
""", height=60)
# 在主内容下放置输入和状态信息
# st.markdown('<div class="content-card">', unsafe_allow_html=True)


# 使用两列布局
col1, col2 = st.columns(2)

with col1:
    video_url = st.text_input(
        "视频链接",
        value="", 
        placeholder="请输入B站视频链接",
        help="输入B站视频链接"
    )

with col2:
    access_token = st.text_input(
        "访问令牌",
        value="", 
        type="password", 
        placeholder="请输入API访问令牌",
        help="输入你的API访问令牌"
    )

# 确保在按钮代码之前应用 CSS
st.markdown("""
    <style>
    div.stButton > button {
        color: white !important;
        background-color: #FB7299 !important;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 按钮代码
submit_button = st.button("🚀 生成思维导图", use_container_width=True, disabled=st.session_state.is_processing)
st.info(f"今日已调用次数: {st.session_state.call_count}/{MAX_CALLS_PER_SESSION} (每日限额)")

# 检查调用限制
def check_call_limits():
    # 检查调用次数限制
    if st.session_state.call_count >= MAX_CALLS_PER_SESSION:
        return False, f"已达到最大调用次数限制（{MAX_CALLS_PER_SESSION}次）。请明天再试。"
    
    return True, ""

# 检查缓存
def check_cache(parameters):
    # 创建参数的唯一键
    cache_key = json.dumps(parameters, sort_keys=True)
    
    if cache_key in st.session_state.cache:
        cached_result = st.session_state.cache[cache_key]
        return True, cached_result, cache_key
    
    return False, None, cache_key

# 尝试调用工作流，最多重试指定次数
def try_run_workflow(coze_api, parameters, max_retries=MAX_RETRY_COUNT):
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            result = coze_api.run_workflow(parameters)
            
            # 检查是否成功
            if not result.get("error") and result.get("code") == 0:
                return result, True
            
            # 记录错误
            last_error = result.get("message", "未知错误")
            
            # 增加重试计数
            retry_count += 1
            
            # 如果还有重试次数，等待一段时间再重试
            if retry_count < max_retries:
                time.sleep(3)  # 等待3秒再重试
        
        except Exception as e:
            # 记录异常
            last_error = str(e)
            
            # 增加重试计数
            retry_count += 1
            
            # 如果还有重试次数，等待一段时间再重试
            if retry_count < max_retries:
                time.sleep(3)  # 等待3秒再重试
    
    # 如果所有重试都失败，返回最后一个错误
    return {"error": True, "message": f"所有尝试都失败: {last_error}"}, False

# 处理工作流调用
if submit_button:
    if not video_url or not access_token:
        st.error("请填写B站视频链接和API访问令牌！")
    else:
        # 解析B站视频链接
        is_valid_url, parsed_url = parse_bilibili_url(video_url)
        
        if not is_valid_url:
            st.error(parsed_url)  # 显示错误信息
        else:
            # 检查调用限制
            can_call, message = check_call_limits()
            
            if not can_call:
                st.error(message)
            else:
                # 设置处理状态为真，禁用按钮
                st.session_state.is_processing = True
                
                # 准备参数
                parameters = {"url": parsed_url}
                
                # 检查缓存
                cached, cached_result, cache_key = check_cache(parameters)
                
                try:
                    if cached:
                        #st.info("使用缓存结果（避免重复调用）")
                        result = cached_result
                    else:
                        # 显示加载状态
                        with st.spinner("正在分析视频并生成思维导图..."):
                            start_time = time.time()
                            coze_api = CozeAPI(access_token, BOT_ID)
                            
                            # 尝试调用工作流，最多重试指定次数
                            result, success = try_run_workflow(coze_api, parameters, MAX_RETRY_COUNT)
                            
                            elapsed_time = time.time() - start_time
                            
                            # 只有在成功调用时才更新调用统计
                            if success:
                                # 更新调用统计
                                st.session_state.call_count += 1
                                st.session_state.last_call_time = datetime.now()
                                
                                # 更新持久化存储
                                update_user_usage(
                                    user_id, 
                                    call_count=st.session_state.call_count,
                                    last_call_time=st.session_state.last_call_time
                                )
                                
                                # 只缓存成功的结果
                                if not result.get("error") and result.get("code") == 0:
                                    st.session_state.cache[cache_key] = result
                                
                                # 记录调用历史
                                call_time = st.session_state.last_call_time.strftime("%H:%M:%S")
                                st.session_state.call_history[call_time] = {
                                    "parameters": parameters,
                                    "result_code": result.get("code", "未知"),
                                    "success": not result.get("error") and result.get("code") == 0,
                                    "elapsed_time": f"{elapsed_time:.2f}秒"
                                }
                                
                                # 更新持久化存储中的调用历史
                                user_usage = get_user_usage(user_id)
                                user_usage["call_history"][call_time] = st.session_state.call_history[call_time]
                                update_user_usage(user_id, call_history=user_usage["call_history"])
                    
                    # 显示结果
                    if result.get("error"):
                        st.error(f"调用失败: {result.get('message')}")
                    else:
                        # 解析并显示工作流数据
                        success, data = parse_workflow_response(result)
                        
                        if success:
                            workflow_data = data
                            st.session_state.result_data = workflow_data
                            st.success("视频分析完成！")
                        else:
                            st.error(f"解析数据失败: {data}")
                            if isinstance(result.get("data"), str):
                                st.subheader("原始数据")
                                st.text_area("", result["data"], height=300, disabled=True, key="raw_data_text_area")
                            else:
                                st.subheader("原始响应")
                                st.json(result)
                
                finally:
                    # 无论成功还是失败，都重置处理状态
                    st.session_state.is_processing = False

# 显示结果区域
if st.session_state.result_data:
    # 确保没有多余的线条或框
    # 检查并移除不必要的 st.markdown 或其他元素

    # 删除多余的分隔线
    # st.markdown('---')  # 如果有多余的分隔线，可以注释掉或删除

    # 确保没有多余的空白框
    # 检查并移除不必要的 st.empty() 或其他空白元素

    # 删除多余的空白元素
    # 确保没有多余的 st.empty() 或其他空白元素

    # 使用容器和CSS确保所有列高度一致
    # st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    workflow_data = st.session_state.result_data
    
    # 思维导图链接
    if "mindmap_url" in workflow_data and workflow_data["mindmap_url"]:
        st.markdown(f'<a href="{workflow_data["mindmap_url"]}" target="_blank" style="background-color: #FB7299; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: block; width: 100%; text-align: center; margin-top: 20px; margin-bottom: 20px;"><span>🔗 在线编辑思维导图</span></a>', unsafe_allow_html=True)
    




    # 思维导图展示区
    if "mindmap_img" in workflow_data and workflow_data["mindmap_img"]:
        try:
            st.markdown(f"""
            <div style="position: relative; display: inline-block; width: 100%;">
                <a href="{workflow_data["mindmap_img"]}" target="_blank" style="position: absolute; top: 10px; right: 0; color: #23ADE5; padding: 3px 8px; text-decoration: none; font-size: 0.8rem;">🔍 查看大图</a>
                <img src="{workflow_data["mindmap_img"]}" style="width: 100%;" alt="生成的思维导图">
            </div>
            """, unsafe_allow_html=True)
        except:
            st.error("无法显示思维导图图片")
    
    # AI总结编辑区
    summary_md = st.text_area(
        "AI总结", 
        value=workflow_data.get("summary", ""), 
        height=300,
        key="summary_edit"
    )

    # 显示预览
    # st.markdown(summary_md, unsafe_allow_html=True)
    
    # 逐字稿编辑区
    transcript_md = st.text_area(
        "视频逐字稿", 
        value=workflow_data.get("transcript", ""), 
        height=300,
        key="transcript_edit"
    )
    

    # CSS 样式
    st.markdown("""
        <style>
        .stTextArea textarea {
            background-color: #F1F2F3;
            color: #FB7299;
            border-radius: 10px;
            border: 1px solid #ddd;
            padding: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    
