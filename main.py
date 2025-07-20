import streamlit as st
import json
import time
from datetime import datetime, timedelta
from coze_api import CozeAPI
from config import BOT_ID, COZE_API_TOKEN, API_URL, EXPECTED_PARAMS
from utils import truncate_text, get_current_time, parse_workflow_response

# 页面配置
st.set_page_config(
    page_title="扣子工作流调用器",
    page_icon="🤖",
    layout="wide"
)

# 初始化会话状态
if 'call_count' not in st.session_state:
    st.session_state.call_count = 0
if 'last_call_time' not in st.session_state:
    st.session_state.last_call_time = None
if 'call_history' not in st.session_state:
    st.session_state.call_history = {}
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# 调用限制配置
MAX_CALLS_PER_SESSION = 10  # 每个会话最大调用次数
COOLDOWN_SECONDS = 5  # 调用冷却时间（秒）

# 标题
st.title("🤖 扣子工作流调用器")
st.markdown("---")

# 侧边栏配置
with st.sidebar:
    st.header("配置信息")
    
    # 工作流配置
    workflow_id = st.text_input("工作流 ID", value=BOT_ID, help="你的工作流 ID")
    access_token = st.text_input("个人访问令牌", value=COZE_API_TOKEN, type="password", help="你的个人访问令牌")
    
    # API 配置
    api_url = API_URL
    
    st.markdown("---")
    st.markdown("### 工作流返回参数")
    for param in EXPECTED_PARAMS:
        st.text(f"• {param}")
    
    # 显示调用统计信息
    st.markdown("---")
    st.markdown("### 调用统计")
    st.text(f"本次会话已调用次数: {st.session_state.call_count}/{MAX_CALLS_PER_SESSION}")
    if st.session_state.last_call_time:
        st.text(f"上次调用时间: {st.session_state.last_call_time.strftime('%H:%M:%S')}")
    st.text(f"缓存条目数: {len(st.session_state.cache)}")
    
    # 添加管理按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("重置调用计数", key="reset_count"):
            st.session_state.call_count = 0
            st.session_state.last_call_time = None
            st.session_state.call_history = {}
            st.success("调用计数已重置！")
            st.rerun()
    
    with col2:
        if st.button("清除结果缓存", key="clear_cache"):
            st.session_state.cache = {}
            st.success("缓存已清除！")
            st.rerun()

# 主要内容区域
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 输入参数")
    
    # 动态参数输入
    st.subheader("工作流参数")
    parameters = {}
    
    # 添加参数的表单
    with st.form("parameters_form"):
        st.write("添加工作流所需的参数：")
        
        # 参数输入区域
        param_count = st.number_input("参数数量", min_value=0, max_value=10, value=1)
        
        for i in range(param_count):
            col_key, col_value = st.columns(2)
            with col_key:
                key = st.text_input(f"参数名 {i+1}", key=f"key_{i}", value="url" if i==0 else "")
            with col_value:
                value = st.text_input(f"参数值 {i+1}", key=f"value_{i}", value="https://www.bilibili.com/video/BV1yp4y1r7hG/" if i==0 else "")
            
            if key and value:
                parameters[key] = value
        
        # 添加强制刷新选项
        force_refresh = st.checkbox("强制刷新（忽略缓存）", value=False)
        
        submit_button = st.form_submit_button("🚀 调用工作流", use_container_width=True)

with col2:
    st.header("📥 返回结果")
    
    # 结果显示区域
    result_placeholder = st.empty()

# 检查调用限制
def check_call_limits():
    # 检查调用次数限制
    if st.session_state.call_count >= MAX_CALLS_PER_SESSION:
        return False, f"已达到最大调用次数限制（{MAX_CALLS_PER_SESSION}次）。请重置计数或稍后再试。"
    
    # 检查冷却时间
    if st.session_state.last_call_time:
        elapsed = datetime.now() - st.session_state.last_call_time
        if elapsed.total_seconds() < COOLDOWN_SECONDS:
            remaining = COOLDOWN_SECONDS - elapsed.total_seconds()
            return False, f"请等待 {remaining:.1f} 秒后再次调用。"
    
    return True, ""

# 检查缓存
def check_cache(parameters):
    # 创建参数的唯一键
    cache_key = json.dumps(parameters, sort_keys=True)
    
    if cache_key in st.session_state.cache:
        cached_result = st.session_state.cache[cache_key]
        return True, cached_result, cache_key
    
    return False, None, cache_key

# 处理工作流调用
if submit_button:
    if not workflow_id or not access_token:
        st.error("请填写工作流 ID 和访问令牌！")
    else:
        # 检查调用限制
        can_call, message = check_call_limits()
        
        if not can_call:
            st.error(message)
        else:
            # 检查缓存
            cached, cached_result, cache_key = check_cache(parameters)
            
            with result_placeholder.container():
                if cached and not force_refresh:
                    st.info("使用缓存结果（避免重复调用）")
                    result = cached_result
                else:
                    # 显示加载状态
                    with st.spinner("正在调用工作流..."):
                        coze_api = CozeAPI(access_token, workflow_id)
                        result = coze_api.run_workflow(parameters)
                        
                        # 更新调用统计
                        st.session_state.call_count += 1
                        st.session_state.last_call_time = datetime.now()
                        
                        # 只缓存成功的结果
                        if not result.get("error") and result.get("code") == 0:
                            st.session_state.cache[cache_key] = result
                        
                        # 记录调用历史
                        st.session_state.call_history[st.session_state.last_call_time.strftime("%H:%M:%S")] = {
                            "parameters": parameters,
                            "result_code": result.get("code", "未知"),
                            "success": not result.get("error") and result.get("code") == 0
                        }
                
                # 显示结果
                if result.get("error"):
                    st.error(f"调用失败: {result.get('message')}")
                else:
                    st.success("工作流调用成功！")
                    
                    # 显示基本信息
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.metric("状态码", result.get("code", "未知"))
                    
                    with col_info2:
                        st.metric("调用时间", get_current_time())
                    
                    # 显示状态信息
                    if result.get("msg"):
                        st.info(f"状态信息: {result.get('msg')}")
                    
                    # 显示调试链接
                    if result.get("debug_url"):
                        st.markdown(f"🔗 [查看调试信息]({result.get('debug_url')})")
                    
                    # 解析并显示工作流数据
                    success, data = parse_workflow_response(result)
                    
                    if success:
                        workflow_data = data
                        st.subheader("工作流输出数据")
                        
                        # 创建标签页显示不同类型的数据
                        tabs = st.tabs(["📊 结构化数据", "🖼️ 图片结果", "📝 文本结果", "🔗 链接结果"])
                        
                        with tabs[0]:
                            st.json(workflow_data)
                        
                        with tabs[1]:
                            # 显示图片相关结果
                            if "mindmap_img" in workflow_data and workflow_data["mindmap_img"]:
                                st.subheader("思维导图图片")
                                try:
                                    st.image(workflow_data["mindmap_img"], caption="生成的思维导图")
                                except:
                                    st.text(f"图片链接: {workflow_data['mindmap_img']}")
                        
                        with tabs[2]:
                            # 显示文本结果
                            if "summary" in workflow_data:
                                st.subheader("摘要")
                                st.text_area("", workflow_data["summary"], height=150, disabled=True, key="summary_text_area")
                            
                            if "transcript" in workflow_data:
                                st.subheader("转录文本")
                                st.text_area("", workflow_data["transcript"], height=150, disabled=True, key="transcript_text_area")
                        
                        with tabs[3]:
                            # 显示链接结果
                            if "mindmap_url" in workflow_data and workflow_data["mindmap_url"]:
                                st.subheader("思维导图链接")
                                st.markdown(f"[🔗 查看思维导图]({workflow_data['mindmap_url']})")
                        
                        # 显示具体的工作流参数
                        st.subheader("具体参数值")
                        expected_results = {
                            "mindmap_img": workflow_data.get("mindmap_img", "未返回"),
                            "mindmap_url": workflow_data.get("mindmap_url", "未返回"),
                            "status_code": workflow_data.get("status_code", "未返回"),
                            "msg": workflow_data.get("msg", "未返回"),
                            "summary": truncate_text(workflow_data.get("summary", "未返回")),
                            "transcript": truncate_text(workflow_data.get("transcript", "未返回"))
                        }
                        
                        for i, (key, value) in enumerate(expected_results.items()):
                            st.text(f"{key}: {value}")
                    else:
                        st.error(f"解析数据失败: {data}")
                        if isinstance(result.get("data"), str):
                            st.subheader("原始数据")
                            st.text_area("", result["data"], height=300, disabled=True, key="raw_data_text_area")
                        else:
                            st.subheader("原始响应")
                            st.json(result)

# 显示调用历史
if st.session_state.call_history and st.checkbox("显示调用历史", value=False):
    st.markdown("---")
    st.subheader("调用历史")
    history_df = {
        "时间": [],
        "参数": [],
        "状态码": [],
        "结果": []
    }
    for time_str, data in st.session_state.call_history.items():
        history_df["时间"].append(time_str)
        history_df["参数"].append(str(data["parameters"]))
        history_df["状态码"].append(data["result_code"])
        history_df["结果"].append("成功" if data.get("success", False) else "失败")
    
    st.dataframe(history_df)

# 页面底部信息
st.markdown("---")
st.markdown("""
### 使用说明

1. **配置信息**：在左侧侧边栏填入你的工作流 ID 和个人访问令牌
2. **输入参数**：根据你的工作流需要，添加相应的输入参数
3. **调用工作流**：点击"调用工作流"按钮执行
4. **查看结果**：在右侧查看工作流的返回结果

### 调用限制说明
- 每个会话最多调用 {0} 次
- 两次调用之间需间隔至少 {1} 秒
- 相同参数的成功调用会使用缓存结果，不会重复请求API
- 可以勾选"强制刷新"选项忽略缓存

### API 接口说明
- **接口地址**: `https://api.coze.cn/v1/workflow/run`
- **请求方式**: POST
- **认证方式**: Bearer Token
- **内容类型**: application/json

### 注意事项
- 确保工作流已经发布
- 访问令牌需要开启工作流 run 权限
- 不支持包含消息节点、流式输出节点、问答节点的工作流
""".format(MAX_CALLS_PER_SESSION, COOLDOWN_SECONDS)) 