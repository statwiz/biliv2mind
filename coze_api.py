import requests
import json
import logging
import os
from datetime import datetime

# 配置日志级别为ERROR，减少不必要的输出
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("CozeAPI")

class CozeAPI:
    def __init__(self, api_url=None, api_token=None, workflow_id=None):
        """
        初始化CozeAPI
        
        参数:
            api_token (str): Coze API令牌
            workflow_id (str): 工作流ID
            api_url (str): API地址
        """
        self.api_url = api_url
        self.api_token = api_token 
        self.workflow_id = workflow_id
        
    def run_workflow(self, parameters=None):
        """
        运行Coze工作流
        
        参数:
            parameters (dict): 工作流参数
            
        返回:
            dict: API响应
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "workflow_id": self.workflow_id
        }
        
        if parameters:
            payload["parameters"] = parameters
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=1200)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": f"API 调用失败: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": True,
                "message": f"请求异常: {str(e)}"
            }
            
    def run_workflow_with_cookies(self, video_url, cookies_dict):
        """
        运行需要cookie的工作流
        
        参数:
            video_url (str): 视频URL
            cookies_dict (dict): B站cookie字典
            
        返回:
            dict: API响应
        """
        # 检查URL格式
        if "bilibili.com/video/" not in video_url:
            return {
                "error": True,
                "message": "URL格式不正确，应包含'bilibili.com/video/'"
            }
        
        # 确保URL不包含不必要的跟踪参数
        clean_url = video_url
        if "?" in clean_url:
            # 保留p参数，删除其他跟踪参数
            base_url, params = clean_url.split("?", 1)
            p_param = None
            param_list = params.split("&")
            for param in param_list:
                if param.startswith("p="):
                    p_param = param
                    break
                    
            if p_param:
                clean_url = f"{base_url}?{p_param}"
            else:
                clean_url = base_url
                
        # 确保必要的cookie字段存在
        required_cookies = ["SESSDATA", "bili_jct", "DedeUserID"]
        for cookie in required_cookies:
            if cookie not in cookies_dict or not cookies_dict[cookie]:
                return {
                    "error": True,
                    "message": f"缺少必要的cookie: {cookie}"
                }
        
        # 使用正确的参数名称 - url 和 cookie
        parameters = {
            "url": clean_url,  # 使用'url'而不是'video_url'
            "cookie": cookies_dict  # 使用'cookie'而不是'cookies_dict'
        }
            
        return self.run_workflow(parameters) 