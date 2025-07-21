import streamlit as st
import json
import time
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from coze_api import CozeAPI
from utils import truncate_text, get_current_time, parse_workflow_response, parse_bilibili_url
import streamlit.components.v1 as components

# 从 .streamlit/secrets.toml 中读取配置
BOT_ID = st.secrets["my_service"]["BOT_ID"]
COZE_API_TOKEN = st.secrets["my_service"]["COZE_API_TOKEN"]
API_URL = st.secrets["my_service"]["API_URL"]
ACCESS_KEY = st.secrets["my_service"]["ACCESS_KEY"]

# 设置页面配置为亮色主题，取消wide模式
st.set_page_config(
    page_title="biliv2mind",
    page_icon="data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTAyNCAxMDI0IiB2ZXJzaW9uPSIxLjEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTc3Ny41MTQ2NjcgMTMxLjY2OTMzM2E1My4zMzMzMzMgNTMuMzMzMzMzIDAgMCAxIDAgNzUuNDM0NjY3TDcyOC43NDY2NjcgMjU1LjgyOTMzM2g0OS45MkExNjAgMTYwIDAgMCAxIDkzOC42NjY2NjcgNDE1Ljg3MnYzMjBhMTYwIDE2MCAwIDAgMS0xNjAgMTYwSDI0NS4zMzMzMzNBMTYwIDE2MCAwIDAgMSA4NS4zMzMzMzMgNzM1Ljg3MnYtMzIwYTE2MCAxNjAgMCAwIDEgMTYwLTE2MGg0OS43NDkzMzRMMjQ2LjQgMjA3LjE0NjY2N2E1My4zMzMzMzMgNTMuMzMzMzMzIDAgMSAxIDc1LjM5Mi03NS40MzQ2NjdsMTEzLjE1MiAxMTMuMTUyYzMuMzcwNjY3IDMuMzcwNjY3IDYuMTg2NjY3IDcuMDQgOC40NDggMTAuOTY1MzMzaDEzNy4wODhjMi4yNjEzMzMtMy45MjUzMzMgNS4xMi03LjY4IDguNDkwNjY3LTExLjAwOGwxMTMuMTA5MzMzLTExMy4xNTJhNTMuMzMzMzMzIDUzLjMzMzMzMyAwIDAgMSA3NS40MzQ2NjcgMHogbTEuMTUyIDIzMS4yNTMzMzRIMjQ1LjMzMzMzM2E1My4zMzMzMzMgNTMuMzMzMzMzIDAgMCAwLTUzLjIwNTMzMyA0OS4zNjUzMzNsLTAuMTI4IDQuMDEwNjY3djMyMGMwIDI4LjExNzMzMyAyMS43NiA1MS4xNTczMzMgNDkuMzY1MzMzIDUzLjE2MjY2NmwzLjk2OCAwLjE3MDY2N2g1MzMuMzMzMzM0YTUzLjMzMzMzMyA1My4zMzMzMzMgMCAwIDAgNTMuMjA1MzMzLTQ5LjM2NTMzM2wwLjEyOC0zLjk2OHYtMzIwYzAtMjkuNDQtMjMuODkzMzMzLTUzLjMzMzMzMy01My4zMzMzMzMtNTMuMzMzMzM0eiBtLTQyNi42NjY2NjcgMTA2LjY2NjY2NmMyOS40NCAwIDUzLjMzMzMzMyAyMy44OTMzMzMgNTMuMzMzMzMzIDUzLjMzMzMzNHY1My4zMzMzMzNhNTMuMzMzMzMzIDUzLjMzMzMzMyAwIDEgMS0xMDYuNjY2NjY2IDB2LTUzLjMzMzMzM2MwLTI5LjQ0IDIzLjg5MzMzMy01My4zMzMzMzMgNTMuMzMzMzMzLTUzLjMzMzMzNHogbTMyMCAwYzI5LjQ0IDAgNTMuMzMzMzMzIDIzLjg5MzMzMyA1My4zMzMzMzMgNTMuMzMzMzM0djUzLjMzMzMzM2E1My4zMzMzMzMgNTMuMzMzMzMzIDAgMSAxLTEwNi42NjY2NjYgMHYtNTMuMzMzMzMzYzAtMjkuNDQgMjMuODkzMzMzLTUzLjMzMzMzMyA1My4zMzMzMzMtNTMuMzMzMzM0eiIgZmlsbD0iI0ZCNzI5OSI+PC9wYXRoPjwvc3ZnPg==",
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
    
    .video-title {
        text-align: center;
        color: #23ADE5 !important;
        font-size: 24px !important;
        font-weight: bold;
        margin-top: 20px !important;
        margin-bottom: 20px !important;
    }
    .section-title {
        font-size: 18px !important;
        color: #23ADE5 !important;
        margin-bottom: 8px !important;
        font-weight: bold;
        margin-top: 25px !important;
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
MAX_CALLS_PER_SESSION = 50  # 每个会话最大调用次数
WORKFLOW_TIMEOUT = 20 * 60  # 工作流执行超时时间（秒）
MAX_RETRY_COUNT = 3  # 最大重试次数

# 确保输入字段和按钮在主标题下正确对齐，标题使用Bilibili粉红色
#st.markdown('<div class="main-header"><h1 style="color: #FB7299 !important;">B站视频思维导图生成器</h1></div>', unsafe_allow_html=True)

components.html("""
    <h1 style=" 
        text-align: center;
        color: #FB7299; font-size: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
    ">
        <svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" width="40" height="40" style="margin-right: 10px;">
            <path d="M777.514667 131.669333a53.333333 53.333333 0 0 1 0 75.434667L728.746667 255.829333h49.92A160 160 0 0 1 938.666667 415.872v320a160 160 0 0 1-160 160H245.333333A160 160 0 0 1 85.333333 735.872v-320a160 160 0 0 1 160-160h49.749334L246.4 207.146667a53.333333 53.333333 0 1 1 75.392-75.434667l113.152 113.152c3.370667 3.370667 6.186667 7.04 8.448 10.965333h137.088c2.261333-3.925333 5.12-7.68 8.490667-11.008l113.109333-113.152a53.333333 53.333333 0 0 1 75.434667 0z m1.152 231.253334H245.333333a53.333333 53.333333 0 0 0-53.205333 49.365333l-0.128 4.010667v320c0 28.117333 21.76 51.157333 49.365333 53.162666l3.968 0.170667h533.333334a53.333333 53.333333 0 0 0 53.205333-49.365333l0.128-3.968v-320c0-29.44-23.893333-53.333333-53.333333-53.333334z m-426.666667 106.666666c29.44 0 53.333333 23.893333 53.333333 53.333334v53.333333a53.333333 53.333333 0 1 1-106.666666 0v-53.333333c0-29.44 23.893333-53.333333 53.333333-53.333334z m320 0c29.44 0 53.333333 23.893333 53.333333 53.333334v53.333333a53.333333 53.333333 0 1 1-106.666666 0v-53.333333c0-29.44 23.893333-53.333333 53.333333-53.333334z" fill="#FB7299"></path>
        </svg>
        B站视频转思维导图
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
        致力于知识分享类视频的思维导图生成
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
    # 用户输入访问密钥
    user_access_key = st.text_input(
        "访问密钥",
        value="", 
        type="password", 
        placeholder="请输入访问密钥",
        help="输入访问密钥以使用应用"
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
    
    div.stButton > button p {
        color: white !important;
    }
    
    div.stButton > button:hover {
        color: white !important;
    }
    
    div.stButton > button span {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.info(f"今日已使用次数: {st.session_state.call_count}/{MAX_CALLS_PER_SESSION} (每日限额)")
# 按钮代码
submit_button = st.button("🚀 一键生成可编辑思维导图", use_container_width=True, disabled=st.session_state.is_processing)

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
    if not video_url or not user_access_key:
        st.error("请填写B站视频链接和访问秘钥！")
    elif user_access_key != ACCESS_KEY:
        st.error("访问秘钥不正确，无法使用应用。")
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
                parameters = {
                    "url": parsed_url,
                    "title": "B站视频思维导图"  # 添加title参数，使用默认值
                }
                
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
                            coze_api = CozeAPI(API_URL, COZE_API_TOKEN, BOT_ID)
                            
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
    
    # 显示视频标题
    if "title" in workflow_data and workflow_data["title"]:
        # 使用bilibili-blue颜色，居中显示，并减小字体
        st.markdown(f'<div class="video-title">{workflow_data["title"]}</div>', unsafe_allow_html=True)

    # 思维导图展示区
    if "mindmap_img" in workflow_data and workflow_data["mindmap_img"]:
        mindmap_url = workflow_data.get("mindmap_url", "")
        online_edit_link = ""
        if mindmap_url:
            online_edit_link = f'<a href="{mindmap_url}" target="_blank" style="position: absolute; top: 10px; left: 10px; color: #fff; background-color: #23ADE5; padding: 3px 8px; text-decoration: none; border-radius: 4px; font-size: 0.8rem;">✍️ 在线编辑</a>'
        
        try:
            st.markdown(f"""
            <div style="position: relative; display: inline-block; width: 100%;">
                {online_edit_link}
                <a href="{workflow_data["mindmap_img"]}" target="_blank" style="position: absolute; top: 10px; right: 10px; color: #fff; background-color: #23ADE5; padding: 3px 8px; text-decoration: none; border-radius: 4px; font-size: 0.8rem;">🔍 查看大图</a>
                <img src="{workflow_data["mindmap_img"]}" style="width: 100%; border-radius: 8px;" alt="生成的思维导图">
            </div>
            """, unsafe_allow_html=True)
        except:
            st.error("无法显示思维导图图片")

    # AI总结编辑区
    st.markdown("<div class='section-title'>AI总结(可以保存成.md文件再导入xmind生成思维导图)</div>", unsafe_allow_html=True)

    # 处理summary内容，去掉markdown格式标记
    summary_content = workflow_data.get("summary", "")
    if summary_content.startswith("```markdown"):
        summary_content = summary_content.replace("```markdown", "", 1)
    if summary_content.endswith("```"):
        summary_content = summary_content[:-3]

    summary_md = st.text_area(
        label="AI总结", 
        value=summary_content, 
        height=400,
        key="summary_edit",
        label_visibility="collapsed"
    )

    # AI总结编辑区
    st.markdown("<div class='section-title'>视频逐字稿</div>", unsafe_allow_html=True)
    transcript_md = st.text_area(
        label="视频逐字稿", 
        value=workflow_data.get("transcript", ""), 
        height=400,
        key="transcript_edit",
        label_visibility="collapsed"
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
    
    
