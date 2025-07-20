import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
BOT_ID = os.getenv('BOT_ID', '')
COZE_API_TOKEN = os.getenv('COZE_API_TOKEN', '')
API_URL = os.getenv('API_URL', 'https://api.coze.cn/v1/workflow/run')

# 工作流预期返回的参数
EXPECTED_PARAMS = [
    "mindmap_img",
    "mindmap_url",
    "status_code",
    "msg",
    "summary",
    "transcript"
] 