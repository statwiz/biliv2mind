import requests
import json
from config import BOT_ID, COZE_API_TOKEN, API_URL

class CozeAPI:
    def __init__(self, api_token=None, workflow_id=None):
        """
        初始化CozeAPI
        
        参数:
            api_token (str): Coze API令牌，默认使用配置文件中的值
            workflow_id (str): 工作流ID，默认使用配置文件中的值
        """
        self.api_url = API_URL
        self.api_token = api_token if api_token else COZE_API_TOKEN
        self.workflow_id = workflow_id if workflow_id else BOT_ID
        
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

# 测试代码
if __name__ == "__main__":
    coze = CozeAPI()
    result = coze.run_workflow({"query": "Python的列表和元组有什么区别?"})
    print(json.dumps(result, ensure_ascii=False, indent=2)) 