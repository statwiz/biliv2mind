import json
from datetime import datetime

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
    if not text:
        return "未返回"
    
    if len(text) > max_length:
        return text[:max_length] + "..."
    
    return text

def get_current_time():
    """
    获取当前时间的格式化字符串
    
    返回:
        str: 格式化的时间字符串
    """
    return datetime.now().strftime("%H:%M:%S")

def parse_workflow_response(response):
    """
    解析工作流响应
    
    参数:
        response (dict): 工作流API响应
        
    返回:
        tuple: (成功标志, 解析后的数据/错误信息)
    """
    if response.get("error"):
        return False, response.get("message", "未知错误")
    
    data = response.get("data")
    if not data:
        return False, "工作流未返回数据"
    
    # 尝试解析JSON数据
    try:
        if isinstance(data, str):
            workflow_data = json.loads(data)
        else:
            workflow_data = data
        return True, workflow_data
    except json.JSONDecodeError:
        return False, "JSON解析错误，原始数据: " + str(data)
    except Exception as e:
        return False, f"解析数据时出错: {str(e)}" 