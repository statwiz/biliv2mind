import json
from datetime import datetime
import time
import re

def format_json(data):
    """
    格式化JSON数据为可读形式
    
    参数:
        data: 要格式化的数据
        
    返回:
        str: 格式化后的JSON字符串
    """
    return json.dumps(data, ensure_ascii=False, indent=2)

def truncate_text(text, max_length=100):
    """
    截断文本，超过最大长度则添加省略号
    
    参数:
        text (str): 要截断的文本
        max_length (int): 最大长度
        
    返回:
        str: 截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def get_current_time():
    """
    获取当前时间的格式化字符串
    
    返回:
        str: 格式化的时间字符串
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_workflow_response(response):
    """
    解析工作流响应
    
    参数:
        response (dict): 工作流API响应
        
    返回:
        tuple: (成功标志, 解析后的数据/错误信息)
    """
    try:
        # 检查响应是否成功
        if response.get("error"):
            return False, f"API调用错误: {response.get('message')}"
        
        # 检查响应码
        if response.get("code") != 0:
            return False, f"工作流执行错误: {response.get('msg')}"
        
        # 获取数据部分
        data = response.get("data")
        
        # 如果数据是字符串，尝试解析为JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return False, "无法解析响应数据为JSON格式"
        
        # 确保数据是字典类型
        if not isinstance(data, dict):
            return False, f"响应数据格式不正确: {type(data)}"
        
        return True, data
    
    except Exception as e:
        return False, f"解析响应时发生错误: {str(e)}"

def parse_bilibili_url(url):
    """
    解析B站视频链接，提取视频ID
    
    参数:
        url (str): B站视频链接
        
    返回:
        tuple: (成功标志, 解析后的视频链接或错误信息)
    """
    try:
        if not url:
            return False, "视频链接不能为空"
            
        # 尝试匹配BV号
        bv_pattern = r'(?:BV|bv)([a-zA-Z0-9]+)'
        bv_match = re.search(bv_pattern, url)
        
        if bv_match:
            bv_id = f"BV{bv_match.group(1)}"
            # 构造标准格式的B站链接
            return True, f"https://www.bilibili.com/video/{bv_id}/"
        
        # 如果没有匹配到BV号，尝试匹配AV号
        av_pattern = r'(?:AV|av)(\d+)'
        av_match = re.search(av_pattern, url, re.IGNORECASE)
        
        if av_match:
            av_id = f"av{av_match.group(1)}"
            return True, f"https://www.bilibili.com/video/{av_id}/"
        
        # 如果都没有匹配到，则认为链接格式不正确
        return False, "无法识别的B站视频链接格式，请确保链接包含正确的BV号或AV号"
    
    except Exception as e:
        return False, f"解析视频链接时发生错误: {str(e)}" 