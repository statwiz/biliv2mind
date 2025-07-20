#!/bin/bash
# 激活conda环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate video

# 检查是否成功激活环境
if [ $? -ne 0 ]; then
    echo "错误：无法激活conda环境'video'。请确保该环境已创建。"
    exit 1
fi

# 检查streamlit是否已安装
if ! command -v streamlit &> /dev/null; then
    echo "错误：streamlit未安装。请运行：conda activate video && pip install streamlit"
    exit 1
fi

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "警告：未找到.env文件，将使用默认设置。"
    echo "如需自定义设置，请创建.env文件并添加以下内容："
    echo "BOT_ID=your_workflow_id_here"
    echo "COZE_API_TOKEN=your_api_token_here"
    echo "API_URL=https://api.coze.cn/v1/workflow/run"
fi

# 启动应用
echo "正在启动B站视频思维导图生成器..."
streamlit run main.py 