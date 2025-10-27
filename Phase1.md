# AI旅行Agent - Phase 1 任务图 (Week 1-8)

核心目标： 验证核心逻辑 (CLI + Streamlit)，L2评估成功率 > 70%

核心交付物： 1. 无UI的API (FastAPI) 2. 简陋的Streamlit内测工具 (app.py)

核心原则： 1. 100%付费API（严禁爬虫） 2. Tracing优先 3. 手动评估优先

### Sprint 1 (Week 1-2): 奠定地基 & 建立“靶场”

**目标：** 基础架构跑通 (DevOps)，评估集准备就绪 (Product)。

|

| 任务ID | 任务类型 | 任务描述 | 关键交付物 | 备注 |

| P1.T1 | DevOps | 技术栈 & 环境设置 | - requirements.txt 文件 - GitHub 私有仓库 - 环境变量 (.env) | pip install fastapi uvicorn streamlit httpx tenacity google-generativeai langsmith-sdk |

| P1.T2 | Infra | 集成Tracing (LangSmith) | - LangSmith 仪表盘 - 一个能看到调用链的 "Hello World" API | Day 1 必须做 (遵照风险点二)。没有这个，后续无法调试。 |

| P1.T3 | Product | 构建 "金丝雀数据集" v1 | - golden_set_v1.json (包含20个Case) | 手动创建 (遵照风险点三)。这是我们未来8周的“靶子”。 |

| P1.T4 | Product | 定义Case结构 | - JSON Schema (输入, 期望输出) | 必须包含对抗Case： 1. 景点闭馆 (如：周一故宫) 2. 恶劣天气 (如下雨) 3. 时间冲突 (用户日历) |

### Sprint 2 (Week 3-4): MVP 1 (API) - 核心逻辑搭建

**目标：** `FastAPI` 接口可以被调用，Multi-Agent 框架 (v0.1) 跑通。

| 任务ID | 任务类型 | 任务描述 | 关键交付物 | 备注 |

| P1.T5 | Backend | Multi-Agent 框架 (v0.1) | - main.py (FastAPI) - agents/ 目录结构 | 定义 CoordinatorAgent 和 ToolsAgent 的基础类。 |

| P1.T6 | Backend | 集成付费API (v1) | - tools/weather.py - tools/poi.py | (遵照风险点四) 100%付费API。集成 OpenWeather 和 Google Places API。 |

| P1.T7 | LLM | 实现 ToolsAgent | - Coordinator 能成功调用 ToolsAgent | 使用Gemini的函数调用 (Function Calling) 功能。 |

| P1.T8 | Test | API 端到端测试 | - POST /generate 接口 | 调用API，能返回一个包含真实天气和POI信息的JSON。在LangSmith上能看到完整调用链。 |

### Sprint 3 (Week 5-6): MVP 1 迭代 & 建立评估流程

**目标：** 开始执行手动评估，L2成功率从0开始提升。

| 任务ID | 任务类型 | 任务描述 | 关键交付物 | 备注 |

| P1.T9 | LLM | 完善 PlannerAgent (v0.1) | - PlannerAgent 的核心 Prompt v1 | 能够根据 ToolsAgent 的输出，生成一个结构化的行程JSON。 |

| P1.T10 | Infra | 建立手动评估流程 | - evaluate.py 脚本 | (遵照风险点三) 脚本功能：循环遍历 golden_set -> 调用API -> 保存所有 results.json。 |

| P1.T11 | QA | 执行 L2 评估 (第1次) | - L2 评估报告 (Excel/Markdown) |

$$
关键任务$$ 周五团队手动对比 results.json 和 golden_set，记录成功率 (e.g., 8/20 = 40%)。 |

| P1.T12 | LLM | 迭代优化 (Cycle 1) | - 失败Case分析报告 - PlannerAgent Prompt v2 | 分析P1.T11中的失败Case，针对性优化Prompt。目标：L2 成功率 > 50%。 |

### Sprint 4 (Week 7-8): MVP 2 (Streamlit) & 准备移交

**目标：** 交付一个简陋但可用的内测工具，L2成功率 > 70%，为Phase 2做准备。

| 任务ID | 任务类型 | 任务描述 | 关键交付物 | 备注 |

| P1.T13 | Frontend | 开发 Streamlit 内测工具 | - app.py (Streamlit App) | (遵照风险点一) 拒绝Next.js。界面只需：输入框、生成按钮、st.json() 显示结果。 |

| P1.T14 | DevOps | 部署 MVP 2 | - Streamlit Community Cloud 链接 - 后端 API 链接 (Cloud Run/VPS) | 确保你的10个专业用户可以访问。 |

| P1.T15 | QA | 执行 L2 评估 (第4次) | - 最终 L2 评估报告 |

$$里程碑$$ L2 评估成功率必须 > 70%。 |

| P1.T16 | PM | 准备 Phase 2 | - 3-5个已锁定的专业用户名单 - 用户访谈问题清单 | 准备好把 P1.T14 的链接发给他们。 |
$$
