# B站视频脚本转思维导图

这是一个使用Streamlit+扣子工作流构建的应用程序，用于B站视频脚本转思维导图。

## 功能特点

- 通过友好的界面调用扣子工作流API
- 支持动态参数输入
- 结果缓存系统，避免重复调用
- 调用限制和冷却时间，控制资源使用
- 调用历史记录
- 结构化展示API返回结果

## 安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/biliv2mind.git
cd biliv2mind
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建一个`.env`文件，包含以下内容：
```
BOT_ID=your_workflow_id_here
COZE_API_TOKEN=your_api_token_here
API_URL=https://api.coze.cn/v1/workflow/run
```

## 使用方法

1. 启动应用
```bash
streamlit run main.py
```

2. 在浏览器中访问应用（默认地址：http://localhost:8501）

3. 输入工作流参数并点击"调用工作流"按钮

## 安全说明

- 敏感信息（如API令牌）存储在`.env`文件中，该文件已被添加到`.gitignore`
- 请勿将包含真实令牌的`.env`文件上传到公共仓库
- 应用中包含调用限制和冷却时间，以控制API使用

## 资源控制

应用实现了多种资源控制机制：

1. **会话调用限制**：每个会话限制最多调用10次
2. **调用冷却时间**：两次调用之间需要间隔至少5秒
3. **结果缓存**：相同参数的成功调用会使用缓存结果
4. **强制刷新选项**：可选择忽略缓存，强制发起新请求

## 文件结构

- `main.py`: 主应用程序文件
- `coze_api.py`: 扣子API调用封装
- `config.py`: 配置文件
- `utils.py`: 工具函数
- `.env`: 环境变量（本地配置，不应上传）
- `requirements.txt`: 依赖列表
