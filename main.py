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

# 设置页面配置
st.set_page_config(
    page_title="BiliBili ⇾ Mind Map",
    page_icon="🌸",
    layout="centered",  
    initial_sidebar_state="collapsed"
)

# --- 全局CSS样式 ---
st.markdown("""
<style>
    :root {
        --bili-pink: #FB7299;
        --bili-blue: #23ADE5;
        --bili-white: #FFFFFF;
        --bili-grey-light: #F6F7F8;
        --bili-grey-mid: #E3E5E7;
        --bili-text-main: #18191C;
        --bili-text-secondary: #61666D;
    }

    /* 隐藏默认的Streamlit页眉和页脚 */
    header, footer { visibility: hidden; }

    /* 全局背景和字体 */
    .stApp {
        background-color: var(--bili-grey-light);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
    }

    /* 主内容容器 */
    .main-container {
        max-width: 720px;
        margin: 2rem auto;
        padding: 2rem 2.5rem;
        background-color: var(--bili-white);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    }

    /* 标题区域 */
    .header-container {
        text-align: center;
        margin-bottom: 2.5rem;
    }
    .header-container h1 {
        color: var(--bili-pink) !important; /* 强制标题为粉色 */
        font-size: 2.2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    .header-container .subtitle {
        color: var(--bili-text-secondary);
        font-size: 1rem;
        margin-top: -8px;
    }
    
    /* --- 自定义输入框样式 (参考B站搜索框) --- */
    div[data-testid="stTextInput"] input,
    div[data-testid="stPasswordInput"] input {
        background-color: var(--bili-grey-light) !important;
        border: 1px solid var(--bili-grey-light) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        color: var(--bili-text-main) !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        width: 100%;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stPasswordInput"] input:focus {
        border-color: var(--bili-pink) !important;
        background-color: var(--bili-white) !important;
    }
    
    /* 按钮样式 */
    .stButton > button {
        width: 100%;
        background-color: var(--bili-pink) !important; /* 纯粉色背景 */
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.2s ease;
        margin-top: 0.5rem;
    }
    .stButton > button:hover {
        opacity: 0.85;
    }
    .stButton > button:disabled {
        opacity: 0.5;
        background: var(--bili-grey-mid) !important;
        cursor: not-allowed;
    }
    
    /* 信息提示框 */
    .stAlert {
        border-radius: 12px !important;
        background-color: #E9F5FE !important; /* 淡蓝色背景 */
        border: none !important;
    }
    .stAlert p {
        color: var(--bili-blue) !important;
        font-weight: 500 !important;
    }

    /* 结果区域 */
    .results-container { margin-top: 2rem; }
    .video-title {
        text-align: center;
        color: var(--bili-text-main) !important;
        font-size: 1.6rem !important;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    
    /* 自定义标签页 */
    div[data-testid="stTabs"] { border: none; }
    div[data-testid="stTabs"] button {
        color: var(--bili-text-secondary);
        border-bottom: 2px solid transparent;
        border-radius: 0;
        font-weight: 600;
        padding: 0.8rem 1rem;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--bili-pink);
        border-bottom: 2px solid var(--bili-pink);
    }

    /* 思维导图图片和链接 */
    .mindmap-container { position: relative; width: 100%; }
    .mindmap-container img { width: 100%; border-radius: 12px; border: 1px solid var(--bili-grey-mid); }
    .mindmap-links { position: absolute; top: 15px; right: 15px; display: flex; gap: 10px; }
    .mindmap-links a {
        color: #fff;
        background-color: rgba(0, 0, 0, 0.5);
        padding: 5px 12px;
        text-decoration: none;
        border-radius: 15px;
        font-size: 0.8rem;
        transition: background-color 0.2s ease;
        font-weight: 500;
    }
    .mindmap-links a:hover { background-color: rgba(0, 0, 0, 0.7); }

    /* 文本区域 */
    .stTextArea textarea {
        background-color: var(--bili-grey-light);
        color: var(--bili-text-main);
        border-radius: 12px;
        border: 1px solid var(--bili-grey-mid);
        padding: 0.75rem;
        height: 450px !important;
    }
</style>
""", unsafe_allow_html=True)


# --- 持久化和用户跟踪逻辑 (无需修改) ---
STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(exist_ok=True)
USAGE_FILE = STORAGE_DIR / "usage_data.pkl"
def get_user_identifier():
    try:
        client_ip = "unknown"
        if hasattr(st, "query_params"): client_ip = st.query_params.get("client_ip", ["unknown"])[0]
        elif hasattr(st, "experimental_get_query_params"): client_ip = st.experimental_get_query_params().get("client_ip", ["unknown"])[0]
    except: pass
    today = datetime.now().strftime("%Y-%m-%d")
    identifier = f"{client_ip}_{today}"
    return hashlib.md5(identifier.encode()).hexdigest()
def load_usage_data():
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, "rb") as f: return pickle.load(f)
        except: return {}
    return {}
def save_usage_data(data):
    with open(USAGE_FILE, "wb") as f: pickle.dump(data, f)
def get_user_usage(user_id):
    usage_data = load_usage_data()
    if user_id not in usage_data:
        usage_data[user_id] = {"call_count": 0, "last_call_time": None, "call_history": {}}
        save_usage_data(usage_data)
    return usage_data[user_id]
def update_user_usage(user_id, call_count=None, last_call_time=None, call_history=None):
    usage_data = load_usage_data()
    if user_id not in usage_data: usage_data[user_id] = {"call_count": 0, "last_call_time": None, "call_history": {}}
    if call_count is not None: usage_data[user_id]["call_count"] = call_count
    if last_call_time is not None: usage_data[user_id]["last_call_time"] = last_call_time
    if call_history is not None: usage_data[user_id]["call_history"] = call_history
    save_usage_data(usage_data)
user_id = get_user_identifier()
user_usage = get_user_usage(user_id)
if 'call_count' not in st.session_state: st.session_state.call_count = user_usage["call_count"]
if 'last_call_time' not in st.session_state: st.session_state.last_call_time = user_usage["last_call_time"]
if 'is_processing' not in st.session_state: st.session_state.is_processing = False
if 'result_data' not in st.session_state: st.session_state.result_data = None
if 'video_url' not in st.session_state: st.session_state.video_url = ""
if 'access_key' not in st.session_state: st.session_state.access_key = ""

# --- 配置 ---
MAX_CALLS_PER_SESSION = 50
MAX_RETRY_COUNT = 3

# --- API 调用和缓存逻辑 (无需修改) ---
def check_call_limits():
    if st.session_state.call_count >= MAX_CALLS_PER_SESSION:
        return False, f"今日调用次数已达上限（{MAX_CALLS_PER_SESSION}次），请明天再来。"
    return True, ""
def check_cache(parameters):
    cache_key = json.dumps(parameters, sort_keys=True)
    return st.session_state.get(cache_key)
def cache_result(key, result):
    st.session_state[key] = result
def try_run_workflow(coze_api, parameters, max_retries=MAX_RETRY_COUNT):
    retry_count = 0
    last_error = None
    while retry_count < max_retries:
        try:
            result = coze_api.run_workflow(parameters)
            if not result.get("error") and result.get("code") == 0:
                return result, True
            last_error = result.get("message", "未知错误")
            retry_count += 1
            if retry_count < max_retries: time.sleep(3)
        except Exception as e:
            last_error = str(e)
            retry_count += 1
            if retry_count < max_retries: time.sleep(3)
    return {"error": True, "message": f"所有尝试均失败: {last_error}"}, False

# --- UI 布局 ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 标题
bili_icon_svg = '<svg viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" width="40" height="40"><path d="M777.514667 131.669333a53.333333 53.333333 0 0 1 0 75.434667L728.746667 255.829333h49.92A160 160 0 0 1 938.666667 415.872v320a160 160 0 0 1-160 160H245.333333A160 160 0 0 1 85.333333 735.872v-320a160 160 0 0 1 160-160h49.749334L246.4 207.146667a53.333333 53.333333 0 1 1 75.392-75.434667l113.152 113.152c3.370667 3.370667 6.186667 7.04 8.448 10.965333h137.088c2.261333-3.925333 5.12-7.68 8.490667-11.008l113.109333-113.152a53.333333 53.333333 0 0 1 75.434667 0z m1.152 231.253334H245.333333a53.333333 53.333333 0 0 0-53.205333 49.365333l-0.128 4.010667v320c0 28.117333 21.76 51.157333 49.365333 53.162666l3.968 0.170667h533.333334a53.333333 53.333333 0 0 0 53.205333-49.365333l0.128-3.968v-320c0-29.44-23.893333-53.333333-53.333333-53.333334z m-426.666667 106.666666c29.44 0 53.333333 23.893333 53.333333 53.333334v53.333333a53.333333 53.333333 0 1 1-106.666666 0v-53.333333c0-29.44 23.893333-53.333333 53.333333-53.333334z m320 0c29.44 0 53.333333 23.893333 53.333333 53.333334v53.333333a53.333333 53.333333 0 1 1-106.666666 0v-53.333333c0-29.44 23.893333-53.333333 53.333333-53.333334z" fill="currentColor"></path></svg>'
st.markdown(f"""
<div class="header-container">
    <h1>{bili_icon_svg} B站视频转思维导图</h1>
    <p class="subtitle">AI 智能解析视频内容，一键生成高清思维导图</p>
</div>
""", unsafe_allow_html=True)

# 输入区域
st.session_state.video_url = st.text_input("url", placeholder="请输入B站视频链接...", label_visibility="collapsed", key="url_input")
st.session_state.access_key = st.text_input("key", type="password", placeholder="请输入您的访问密钥", label_visibility="collapsed", key="key_input")

# 按钮和使用情况
submit_button = st.button("🚀 一键生成", use_container_width=True, disabled=st.session_state.is_processing)
st.info(f"今日已使用: {st.session_state.call_count}/{MAX_CALLS_PER_SESSION} 次")

# --- 按钮提交逻辑 ---
if submit_button:
    if not st.session_state.video_url or not st.session_state.access_key:
        st.error("请输入B站视频链接和访问密钥！")
    elif st.session_state.access_key != ACCESS_KEY:
        st.error("访问密钥不正确！")
    else:
        is_valid_url, parsed_url = parse_bilibili_url(st.session_state.video_url)
        if not is_valid_url:
            st.error(parsed_url)
        else:
            can_call, message = check_call_limits()
            if not can_call:
                st.error(message)
            else:
                parameters = {"url": parsed_url, "title": "B站视频思维导图"}
                cache_key = json.dumps(parameters, sort_keys=True)
                cached_result = check_cache(cache_key)
                
                if cached_result:
                    st.session_state.result_data = cached_result
                else:
                    st.session_state.is_processing = True
                st.rerun()

# --- 处理和结果展示 ---
if st.session_state.is_processing:
    with st.spinner("🧠 AI正在解析视频，请稍候..."):
        is_valid_url, parsed_url = parse_bilibili_url(st.session_state.video_url)
        parameters = {"url": parsed_url, "title": "B站视频思维导图"}
        cache_key = json.dumps(parameters, sort_keys=True)
        
        coze_api = CozeAPI(API_URL, COZE_API_TOKEN, BOT_ID)
        result, success = try_run_workflow(coze_api, parameters, MAX_RETRY_COUNT)

        if success:
            st.session_state.call_count += 1
            st.session_state.last_call_time = datetime.now()
            update_user_usage(user_id, call_count=st.session_state.call_count, last_call_time=st.session_state.last_call_time)
            
            parse_success, data = parse_workflow_response(result)
            if parse_success:
                st.session_state.result_data = data
                cache_result(cache_key, data)
            else:
                st.session_state.result_data = {"error": True, "message": data, "raw": result}
        else:
             st.session_state.result_data = {"error": True, "message": result.get("message")}
        
        st.session_state.is_processing = False
        st.rerun()

if st.session_state.result_data:
    if st.session_state.result_data.get("error"):
        st.error(f"处理失败: {st.session_state.result_data.get('message')}")
        if 'raw' in st.session_state.result_data: st.json(st.session_state.result_data['raw'])
    else:
        st.success("视频分析完成！")
        workflow_data = st.session_state.result_data
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        
        if "title" in workflow_data and workflow_data["title"]:
            st.markdown(f'<div class="video-title">{workflow_data["title"]}</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["🧠 思维导图", "📄 AI总结", "📝 逐字稿"])

        with tab1:
            if "mindmap_img" in workflow_data and workflow_data["mindmap_img"]:
                mindmap_url = workflow_data.get("mindmap_url", "")
                edit_link = f'<a href="{mindmap_url}" target="_blank">✍️ 在线编辑</a>' if mindmap_url else ""
                view_link = f'<a href="{workflow_data["mindmap_img"]}" target="_blank">🔍 查看大图</a>'
                
                st.markdown(f"""
                <div class="mindmap-container">
                    <div class="mindmap-links">{edit_link}{view_link}</div>
                    <img src="{workflow_data["mindmap_img"]}" alt="生成的思维导图">
                </div>
                """, unsafe_allow_html=True)
                st.caption("提示：下方的“AI总结”Markdown文本也可以直接导入Xmind等工具生成思维导图。")
            else:
                st.warning("未能生成思维导图图片。")

        with tab2:
            summary_content = workflow_data.get("summary", "未能生成AI总结。")
            if summary_content.startswith("```markdown"): summary_content = summary_content.replace("```markdown", "", 1).strip()
            if summary_content.endswith("```"): summary_content = summary_content[:-3].strip()
            st.text_area("AI总结", value=summary_content, label_visibility="collapsed")

        with tab3:
            transcript_content = workflow_data.get("transcript", "未能获取视频逐字稿。")
            st.text_area("视频逐字稿", value=transcript_content, label_visibility="collapsed")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
    
    

