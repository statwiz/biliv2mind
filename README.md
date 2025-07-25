
# biliv2mind: B站视频转思维导图

biliv2mind 是一个使用 Streamlit 构建的Web应用，可以快速将Bilibili视频内容转换为可编辑的思维导图、AI总结和视频逐字稿，特别适用于知识分享类视频。

## ✨ 功能特性

- **一键转换**: 输入B站视频链接，即可生成思维导图。
- **多种输出**:
    - **思维导图图片**: 直观查看视频内容结构。
    - **在线编辑链接**: 在线编辑和调整生成的思维导图。
    - **AI总结 (Markdown)**: 将视频核心内容总结为Markdown格式，可直接导入XMind等思维导图软件。
    - **视频逐字稿**: 获取完整的视频文字记录。
- **双API支持**: 支持两种API调用模式，可靠性更高:
    - **主API**: 使用B站cookie提取视频信息
    - **备用API**: 当主API失败时自动回退使用
- **使用限制**: 为了防止滥用，应用对每个用户（基于IP）设置了每日调用次数限制。
- **缓存机制**: 对已处理过的视频链接会进行缓存，加快访问速度并节省资源。

## 🚀 如何使用

1. 访问应用部署的网址。
2. 在 "视频链接" 输入框中粘贴一个Bilibili视频的URL（支持带分P参数）。
3. 在 "访问密钥" 输入框中输入正确的访问密钥。
4. 点击 "🚀 一键生成" 按钮。
5. 等待几分钟，应用处理完成后即可在下方看到结果。

## 🛠️ 本地开发

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/biliv2mind.git
cd biliv2mind
```

### 2. 环境设置

本项目使用 `conda` 管理环境。

```bash
conda create --name video python=3.9
conda activate video
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录下创建一个 `.streamlit` 文件夹，并在其中创建一个 `secrets.toml` 文件，内容如下：

```toml
[my_service]
# 原有API配置
BOT_ID = "原BOT_ID"
COZE_API_TOKEN = "你的COZE_API_TOKEN"
API_URL = "https://api.coze.cn/v1/workflow/run"
ACCESS_KEY = "你的ACCESS_KEY"

# 新API配置
NEW_BOT_ID = "新BOT_ID"

# B站Cookie配置
SESSDATA = "你的SESSDATA"
bili_jct = "你的bili_jct"
DedeUserID = "你的DedeUserID"
DedeUserID__ckMd5 = "你的DedeUserID__ckMd5"  # 可选
sid = "你的sid"  # 可选
buvid3 = "你的buvid3"  # 可选
buvid_fp = "你的buvid_fp"  # 可选
```

请将配置中的占位符替换为你的实际配置值。

### 5. 运行应用

```bash
chmod +x start.sh
./start.sh
```
或直接运行:
```bash
conda activate video
streamlit run main.py
```

## 📂 项目结构

```
.
├── main.py             # Streamlit 应用主文件
├── coze_api.py         # 封装 Coze API 调用的类
├── utils.py            # 包含辅助函数，如URL解析、响应解析等
├── requirements.txt    # 项目依赖
├── start.sh            # 启动脚本
├── storage/            # 存储持久化数据，如用户使用记录和结果缓存
└── .streamlit/
    └── secrets.toml    # (部署用)存放敏感配置信息
```