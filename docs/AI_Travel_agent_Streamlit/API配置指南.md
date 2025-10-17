# 🔑 API 配置指南

## 📋 目录
1. [API 概述](#api-概述)
2. [OpenAI API 配置](#openai-api-配置)
3. [Google Serper API 配置](#google-serper-api-配置)
4. [OpenWeatherMap API 配置](#openweathermap-api-配置)
5. [环境变量配置](#环境变量配置)
6. [API 使用限制与定价](#api-使用限制与定价)
7. [故障排除](#故障排除)

---

## 🌐 API 概述

本项目使用以下三个主要 API:

| API | 优先级 | 用途 | 费用 |
|-----|--------|------|------|
| **OpenAI API** | 🔴 必需 | GPT-4 模型，处理用户查询 | 付费 (按使用量) |
| **Google Serper API** | 🟡 推荐 | 搜索酒店、景点、餐厅等信息 | 免费额度 + 付费 |
| **OpenWeatherMap API** | 🟢 可选 | 获取目的地天气信息 | 免费额度 + 付费 |

### API 优先级说明

- **🔴 必需**: 没有此 API，应用无法运行
- **🟡 推荐**: 如果没有，会使用备用方案 (DuckDuckGo 搜索)
- **🟢 可选**: 如果没有，相关功能会被禁用

---

## 🤖 OpenAI API 配置

### 1. 获取 API Key

#### 步骤 1: 注册 OpenAI 账户
1. 访问 [OpenAI 官网](https://platform.openai.com)
2. 点击 "Sign Up" 注册账户
3. 验证您的邮箱和手机号码

#### 步骤 2: 充值账户
1. 登录后，访问 [Billing](https://platform.openai.com/account/billing)
2. 点击 "Add payment method" 添加支付方式
3. 充值至少 5-10 美元 (推荐从 20 美元开始)

#### 步骤 3: 创建 API Key
1. 访问 [API Keys 页面](https://platform.openai.com/api-keys)
2. 点击 "Create new secret key"
3. 给 Key 起个名字 (如 "Travel Agent App")
4. **立即复制并保存 Key** (只会显示一次!)

```
示例 API Key 格式:
sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. 配置说明

在 `.env` 文件中添加:
```env
OPENAI_API_KEY=sk-proj-your_actual_key_here
```

### 3. 模型选择

项目默认使用 **GPT-4o** 模型:
```python
llm = ChatOpenAI(
    model="gpt-4o",          # 最新的 GPT-4 优化模型
    temperature=0,           # 确定性输出
    max_tokens=2000,         # 最大输出长度
    api_key=openai_api_key
)
```

#### 可用模型对比

| 模型 | 速度 | 成本 | 质量 | 推荐场景 |
|------|------|------|------|----------|
| **gpt-4o** | 快 | 中等 | 优秀 | **推荐使用** (性价比最高) |
| gpt-4-turbo | 中 | 高 | 优秀 | 需要最高质量时 |
| gpt-3.5-turbo | 很快 | 低 | 良好 | 预算紧张时 |

#### 切换到其他模型

编辑 `streamlit_app.py:122`:
```python
# 使用 GPT-3.5 (更便宜)
llm = ChatOpenAI(model="gpt-3.5-turbo", ...)

# 使用 GPT-4 Turbo (更强大)
llm = ChatOpenAI(model="gpt-4-turbo", ...)
```

### 4. 费用估算

#### GPT-4o 定价 (2024)
- **输入**: $5 / 1M tokens
- **输出**: $15 / 1M tokens

#### 单次查询成本估算
典型的旅行查询:
- 输入 tokens: ~500 (系统提示词 + 用户查询 + 工具结果)
- 输出 tokens: ~2000 (详细的旅行计划)

**成本计算**:
```
输入成本: 500 tokens × $5/1M = $0.0025
输出成本: 2000 tokens × $15/1M = $0.03
总成本: ~$0.033 (约 0.23 元人民币)
```

**月度预算建议**:
- 轻度使用 (30 次/月): ~$1 (7 元)
- 中度使用 (100 次/月): ~$3.3 (23 元)
- 重度使用 (500 次/月): ~$16.5 (115 元)

### 5. 监控使用量

#### 在 OpenAI 控制台监控
1. 访问 [Usage Dashboard](https://platform.openai.com/usage)
2. 查看每日/每月使用量
3. 设置使用限额:
   - Settings → Limits → Set monthly budget

#### 在代码中添加监控
```python
# 获取使用情况
response = llm.invoke(...)
if hasattr(response, 'usage'):
    st.sidebar.metric("Tokens Used", response.usage.total_tokens)
```

---

## 🔍 Google Serper API 配置

### 1. 获取 API Key

#### 步骤 1: 注册账户
1. 访问 [Serper.dev](https://serper.dev)
2. 点击 "Sign Up" 或 "Get Started"
3. 使用 Google 账号登录

#### 步骤 2: 获取免费额度
- **免费额度**: 2,500 次搜索/月
- 无需信用卡即可开始使用

#### 步骤 3: 复制 API Key
1. 登录后，在 Dashboard 中找到 API Key
2. 复制 API Key

```
示例 API Key 格式:
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

### 2. 配置说明

在 `.env` 文件中添加:
```env
SERPER_API_KEY=your_serper_api_key_here
```

### 3. 备用方案

如果没有配置 Serper API，系统会自动使用 **DuckDuckGo** 作为备用:
```python
def search_google(query: str) -> str:
    try:
        serper_api_key = st.secrets.get("SERPER_API_KEY") or os.getenv("SERPER_API_KEY")
        if serper_api_key:
            # 使用 Google Serper
            search_serper = GoogleSerperAPIWrapper()
            return search_serper.run(query)
        else:
            # 回退到 DuckDuckGo
            return search_duck(query)
    except Exception as e:
        return f"Search failed: {str(e)}"
```

### 4. 费用说明

#### 定价
- **免费**: 2,500 次搜索/月
- **Paid**: $50/月 (100,000 次搜索)

对于个人项目，免费额度通常足够。

---

## 🌤️ OpenWeatherMap API 配置

### 1. 获取 API Key

#### 步骤 1: 注册账户
1. 访问 [OpenWeatherMap](https://openweathermap.org)
2. 点击 "Sign Up" 注册
3. 验证邮箱

#### 步骤 2: 创建 API Key
1. 登录后，访问 [API Keys](https://home.openweathermap.org/api_keys)
2. 系统会自动创建一个默认 Key
3. 或者点击 "Generate" 创建新 Key
4. 复制 API Key

```
示例 API Key 格式:
1234567890abcdef1234567890abcdef
```

**重要**: 新创建的 API Key 可能需要 1-2 小时才能激活

### 2. 配置说明

在 `.env` 文件中添加:
```env
OPENWEATHERMAP_API_KEY=your_weather_api_key_here
```

### 3. 功能说明

如果配置了天气 API，用户可以:
- 获取目的地实时天气
- 查看温度、湿度、风速等详细信息
- 获取天气建议 (如是否适合户外活动)

如果没有配置:
- 天气功能会被禁用
- 侧边栏会显示 "⚠️ Weather API Missing"
- 不影响其他功能的使用

### 4. 费用说明

#### 免费计划
- **免费**: 1,000 次调用/天
- 60 次调用/分钟
- 完全免费，无需信用卡

对于个人项目，免费计划完全足够。

---

## ⚙️ 环境变量配置

### 1. 本地开发配置

#### 创建 .env 文件

在项目根目录创建 `.env` 文件:

```env
# OpenAI API (必需)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Serper API (推荐)
SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenWeatherMap API (可选)
OPENWEATHERMAP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 配置注意事项

1. **不要提交到 Git**:
   - 确保 `.env` 在 `.gitignore` 中
   - 永远不要把 API Key 提交到代码仓库

2. **格式正确**:
   - `=` 两边不要有空格
   - 不需要引号
   - 一行一个配置

3. **验证配置**:
```python
# 在 Python 中测试
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("OPENAI_API_KEY"))  # 应该输出你的 Key
```

### 2. Streamlit Cloud 配置

部署到 Streamlit Cloud 时，使用 Secrets 管理:

#### 步骤 1: 进入 Secrets 设置
1. 打开你的应用
2. 点击右上角 "⋮" → "Settings"
3. 选择 "Secrets"

#### 步骤 2: 添加 Secrets
使用 TOML 格式:

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-proj-your_key_here"
SERPER_API_KEY = "your_serper_key_here"
OPENWEATHERMAP_API_KEY = "your_weather_key_here"
```

#### 步骤 3: 代码中读取
应用已经配置好自动读取:
```python
openai_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
```
优先从 Streamlit Secrets 读取，回退到环境变量。

### 3. 其他部署平台

#### Heroku
```bash
heroku config:set OPENAI_API_KEY=your_key_here
heroku config:set SERPER_API_KEY=your_key_here
heroku config:set OPENWEATHERMAP_API_KEY=your_key_here
```

#### Railway
在 Railway Dashboard 的 Variables 中添加。

#### Docker
使用 docker-compose.yml:
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - SERPER_API_KEY=${SERPER_API_KEY}
  - OPENWEATHERMAP_API_KEY=${OPENWEATHERMAP_API_KEY}
```

---

## 💰 API 使用限制与定价

### 1. OpenAI API

#### Rate Limits (速率限制)
- **GPT-4o**:
  - 10,000 TPM (tokens per minute)
  - 500 RPM (requests per minute)
- **GPT-3.5-turbo**:
  - 90,000 TPM
  - 3,500 RPM

#### 定价总结
| 模型 | 输入 ($/1M tokens) | 输出 ($/1M tokens) |
|------|-------------------|-------------------|
| GPT-4o | $5 | $15 |
| GPT-4-turbo | $10 | $30 |
| GPT-3.5-turbo | $0.5 | $1.5 |

#### 节省成本的建议
1. **减少 max_tokens**:
   ```python
   max_tokens=1000  # 而不是 2000
   ```

2. **使用更短的系统提示词**: 移除不必要的说明

3. **缓存结果**:
   ```python
   @st.cache_data
   def get_travel_plan(query):
       # ...
   ```

4. **切换到 GPT-3.5**: 成本降低 90%

### 2. Google Serper API

#### 免费额度
- 2,500 次搜索/月
- 无需信用卡
- 每次搜索返回 10 个结果

#### 付费计划
- $50/月: 100,000 次搜索
- 适合高流量应用

### 3. OpenWeatherMap API

#### 免费额度
- 1,000 次调用/天 (30,000 次/月)
- 60 次/分钟
- 完全免费

#### 付费计划
- 适合企业级应用
- 更高的调用频率
- 更多天气数据

---

## 🔧 故障排除

### 1. OpenAI API 问题

#### 错误: "Invalid API key"
**症状**:
```
Error: Incorrect API key provided
```

**解决方案**:
1. 检查 Key 是否正确复制 (无多余空格)
2. 确认 Key 以 `sk-` 开头
3. 验证 Key 在 OpenAI Dashboard 中仍然有效
4. 检查账户是否有余额

#### 错误: "Rate limit exceeded"
**症状**:
```
Error: Rate limit reached for requests
```

**解决方案**:
1. 等待 1 分钟后重试
2. 减少并发请求
3. 考虑升级 OpenAI 账户等级
4. 实现请求队列

#### 错误: "Insufficient quota"
**症状**:
```
Error: You exceeded your current quota
```

**解决方案**:
1. 访问 [Billing](https://platform.openai.com/account/billing)
2. 充值账户
3. 检查月度限额设置

### 2. Serper API 问题

#### 错误: "API key not found"
**症状**:
```
Search failed: 401 Unauthorized
```

**解决方案**:
1. 验证 `SERPER_API_KEY` 是否正确配置
2. 检查 Key 是否激活
3. 确认没有超出免费额度

#### 自动回退到 DuckDuckGo
如果 Serper 失败，应用会自动使用 DuckDuckGo:
```python
# 无需任何配置，自动工作
search_result = search_duck(query)
```

### 3. Weather API 问题

#### 错误: "City not found"
**症状**:
```
Weather data unavailable: 404 Not Found
```

**解决方案**:
1. 检查城市名称拼写 (使用英文)
2. 尝试使用城市的常用英文名称
   - 例: "Beijing" 而不是 "北京"

#### 错误: "API key not activated"
**症状**:
```
Error: 401 Unauthorized
```

**解决方案**:
1. 等待 1-2 小时让 API Key 激活
2. 验证邮箱是否已确认
3. 重新生成新的 API Key

### 4. 环境变量问题

#### 问题: 环境变量未加载
**症状**:
```python
os.getenv("OPENAI_API_KEY")  # 返回 None
```

**解决方案**:
1. 确认 `.env` 文件在项目根目录
2. 检查文件名是否正确 (不是 `.env.txt`)
3. 重新启动应用
4. 验证 `python-dotenv` 已安装

#### 问题: Streamlit Secrets 未生效
**症状**:
```python
st.secrets.get("OPENAI_API_KEY")  # 返回 None
```

**解决方案**:
1. 检查 Secrets 格式是否为 TOML
2. 确认没有语法错误
3. 重新部署应用
4. 清除浏览器缓存

---

## 📊 API 使用最佳实践

### 1. 安全性
- ✅ 使用环境变量存储 API Key
- ✅ 永远不要提交 `.env` 到 Git
- ✅ 定期轮换 API Key
- ✅ 为不同项目使用不同的 Key
- ❌ 不要在代码中硬编码 API Key
- ❌ 不要在日志中记录 API Key

### 2. 成本控制
- ✅ 设置月度预算上限
- ✅ 监控每日使用量
- ✅ 实现请求缓存
- ✅ 使用合适的模型 (不一定要最贵的)
- ❌ 不要设置无限制的自动化任务
- ❌ 不要在循环中无限调用 API

### 3. 性能优化
- ✅ 缓存不变的结果
- ✅ 批量处理请求
- ✅ 使用异步调用 (如果需要)
- ✅ 实现错误重试机制
- ❌ 不要同步等待多个 API 调用
- ❌ 不要忽略 API 的速率限制

---

## 🧪 测试 API 配置

### 快速测试脚本

创建 `test_apis.py`:

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import OpenWeatherMapAPIWrapper, GoogleSerperAPIWrapper

load_dotenv()

def test_openai():
    """测试 OpenAI API"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API Key 未配置")
            return False

        llm = ChatOpenAI(api_key=api_key, model="gpt-4o")
        response = llm.invoke("Hello!")
        print("✅ OpenAI API 工作正常")
        return True
    except Exception as e:
        print(f"❌ OpenAI API 错误: {str(e)}")
        return False

def test_serper():
    """测试 Serper API"""
    try:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            print("⚠️ Serper API Key 未配置 (将使用 DuckDuckGo)")
            return True

        os.environ["SERPER_API_KEY"] = api_key
        search = GoogleSerperAPIWrapper()
        result = search.run("test")
        print("✅ Serper API 工作正常")
        return True
    except Exception as e:
        print(f"⚠️ Serper API 错误: {str(e)} (将使用 DuckDuckGo)")
        return True

def test_weather():
    """测试 Weather API"""
    try:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            print("⚠️ Weather API Key 未配置 (天气功能将禁用)")
            return True

        os.environ["OPENWEATHERMAP_API_KEY"] = api_key
        weather = OpenWeatherMapAPIWrapper()
        result = weather.run("London")
        print("✅ Weather API 工作正常")
        return True
    except Exception as e:
        print(f"⚠️ Weather API 错误: {str(e)} (天气功能将禁用)")
        return True

if __name__ == "__main__":
    print("🧪 开始测试 API 配置...\n")

    openai_ok = test_openai()
    print()
    serper_ok = test_serper()
    print()
    weather_ok = test_weather()
    print()

    if openai_ok:
        print("🎉 所有必需的 API 都配置正确!")
        print("✅ 可以开始使用应用了")
    else:
        print("⚠️ 请先配置 OpenAI API Key")
```

运行测试:
```bash
python test_apis.py
```

---

## 📚 相关资源

- [OpenAI API 文档](https://platform.openai.com/docs)
- [Serper API 文档](https://serper.dev/api)
- [OpenWeatherMap API 文档](https://openweathermap.org/api)
- [LangChain 文档](https://python.langchain.com)
- [Streamlit Secrets 管理](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**最后更新**: 2025-10-17
**文档版本**: 1.0.0
