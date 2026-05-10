# 问渠 — AI 保研学术面试官

> 问渠那得清如许，为有源头活水来。——朱熹《观书有感》

---

## 项目简介

**问渠**是一个专注于计算机系保研复试（预推免/夏令营）的 AI 模拟面试系统。它模拟严苛博导风格，对学生的科研项目进行"剥洋葱式"连续追问，帮助学生提前暴露项目经历中的逻辑漏洞和知识盲区。

本项目基于 [Open WebUI](https://github.com/open-webui/open-webui) 二次开发，在保留原有 LLM 对话能力的基础上，新增独立的保研复试模拟面试模块。

---

## 目标用户

**计算机系保研复试学生**，尤其是：
- 有科研/实验室/论文经历
- 简历内容较强但表达能力薄弱
- 容易在导师深挖项目细节时暴露逻辑漏洞
- 缺乏高质量、持续追问式模拟训练

---

## 核心功能

### 完整面试闭环

```
简历上传 → 项目解析 → 风险评分 → 多轮追问 → 反馈报告
```

1. **简历解析** — 上传 PDF 简历，AI 自动提取科研项目、论文、技能等信息
2. **项目评分** — 自动识别最容易被导师深挖的高风险项目，从原理理解、技术选型、实验设计等维度打分
3. **多轮压力面试** — AI 扮演严格博导进行 3-5 轮连续追问，由浅入深，根据回答灵活调整追问方向
4. **卡壳检测** — 当学生答不出时自动切换角度，不浪费时间死磕
5. **反馈报告** — 从学术深度、表达清晰度、真实性风险三个维度评分，附带漏洞分析和改进建议

---

## 产品差异化

本产品不是普通 AI 问答机器人，而是：

| 维度 | 问渠 | 通用 ChatGPT |
|------|------|-------------|
| 场景 | 保研复试科研追问专精 | 通用对话 |
| 追问 | 强制 3-5 轮连续深挖 | 单轮问答 |
| 风格 | 严苛博导，持续施压 | 温和鼓励 |
| 评分 | 三维度量化评估 | 无 |
| 流程 | 简历→选择项目→追问→报告 | 自由对话 |

---

## 技术架构

### 技术栈

| 层 | 技术 |
|---|---|
| 前端 | SvelteKit 5 + TypeScript + TailwindCSS 4 |
| 后端 | Python FastAPI + SQLAlchemy (async) |
| 数据库 | SQLite / PostgreSQL |
| LLM | DeepSeek API（OpenAI 兼容） |
| 部署 | Docker / 本地开发 |
| 基础设施 | 复用 Open WebUI 的用户认证、文件管理、LLM 连接层 |

### 项目结构

```
liya-ai/
├── wenqu/README.md               # 问渠模块说明
├── src/
│   ├── routes/wenqu/              # 问渠前端页面
│   │   ├── +page.svelte           # Landing 页（首页）
│   │   ├── upload/                # 简历上传页
│   │   ├── interview/             # 面试对话页
│   │   ├── report/                # 反馈报告页
│   │   └── history/               # 历史记录页
│   └── lib/apis/wenqu/            # 问渠 API 客户端
├── backend/open_webui/
│   ├── routers/wenqu.py           # API 路由 (/api/v1/wenqu/*)
│   ├── models/wenqu.py            # 数据模型
│   └── utils/wenqu_engine/        # 追问引擎核心
│       ├── resume_parser.py       # 简历解析
│       ├── project_selector.py    # 项目风险评分
│       ├── question_engine.py     # 多轮追问（含卡壳检测）
│       ├── feedback_engine.py     # 反馈报告生成
│       └── deepseek_client.py     # DeepSeek API 客户端
```

### 隔离设计

问渠模块以 **独立路径** 方式集成：
- 前端路由 `/wenqu/*`，与原有聊天界面完全隔离
- 后端 API `/api/v1/wenqu/*`，独立 router
- 数据表 `wenqu_session`、`wenqu_round`、`wenqu_feedback_report`，不与原有数据交叉
- 不修改任何 Open WebUI 原有代码，仅新增文件 + 2 行注册代码

---

## 本地运行

### 前置条件

- Node.js >= 18
- Python 3.11 - 3.12
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 快速启动

```bash
# 1. 复制环境变量
cp .env.example .env
# 在 .env 中填入 DEEPSEEK_API_KEY

# 2. 安装后端依赖
uv sync

# 3. 安装前端依赖
npm install

# 4. 启动前端 dev server
npm run dev

# 5. 新终端，启动后端
source .venv/bin/activate
uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload
```

启动后访问 **http://localhost:5173** 进入问渠首页。

---

## 开发说明

### 与 Open WebUI 的关系

- **fork 来源**：[Open WebUI](https://github.com/open-webui/open-webui) v0.9.2
- **fork 保留功能**：用户认证、LLM 连接（Ollama/OpenAI）、文件管理、聊天界面
- **新增原创代码**：问渠整个模块（`wenqu/`、`src/routes/wenqu/`、`backend/.../wenqu*`）

### 刻意不做

- ❌ AI 语音输出 (TTS)
- ❌ 视频面试
- ❌ 泛化求职八股
- ❌ 非计算机专业场景
- ❌ 多用户复杂系统
- ❌ 排行榜/社交功能

### 后续方向

- 语音输入（ASR）
- 支持更多 LLM 后端（Ollama 本地模型）
- 用户自建题库
- 面试记录对比分析

---

## License

本项目包含 Open WebUI 的原始代码（基于 [Open WebUI License](./LICENSE)），以及问渠模块的原创代码。
