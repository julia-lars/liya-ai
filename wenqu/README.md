# 问渠 — AI 保研学术面试官（Wenqu Module for liya-ai）

> 问渠那得清如许，为有源头活水来。——朱熹《观书有感》

---

## 1. 概述

**问渠**是 liya-ai（Open WebUI fork）中的一个独立模块，专注计算机系保研复试（预推免/夏令营）的**科研真实性压力测试**。

与 liya-ai 主体（通用 LLM 聊天界面）隔离部署，通过独立的 `/wenqu/*` 路由访问。共享 liya-ai 的用户认证、LLM 连接、文件上传等基础设施。

---

## 2. 目标用户

**计算机系保研复试学生**，尤其是：
- 有科研/实验室/论文经历
- 简历内容较强但表达能力薄弱
- 容易在导师深挖项目细节时暴露逻辑漏洞
- 缺乏高质量、持续追问式模拟训练

---

## 3. 核心价值

打造一个专注于 **计算机科研项目真实性与深度拷问** 的 AI 模拟导师系统，帮助学生提前适应：
- 项目真实性审查
- 技术细节追问
- 实验设计质询
- Failure case 分析
- 改进能力考察
- 学术表达优化

---

## 4. MVP 闭环流程

```
科研简历 → 深度追问 → 高质量反馈
```

### Step 1：简历上传
- 用户上传 PDF 简历（复用 liya-ai 文件上传能力）

### Step 2：简历解析
AI 自动提取：科研项目、论文发表、技术栈、比赛/实验经历

### Step 3：高价值项目锁定
AI 自动识别"最容易在保研复试中被导师深挖的项目"

### Step 4：导师级压力面试
AI 扮演严苛导师，对单一项目连续追问 3-5 轮：
- 原理、模型结构、技术选型
- Baseline、实验设计、Failure cases
- 改进方向、Ablation Study

### Step 5：学生回答方式
- 文本输入（主）
- 语音输入（ASR，加分项）

### Step 6：反馈报告
- Academic Depth Score
- Expression Clarity Score
- Authenticity Risk Score
- 导师视角漏洞分析
- 改进建议

---

## 5. 技术架构（基于 liya-ai）

### 前端
- **SvelteKit 5** + TypeScript + TailwindCSS 4（与 liya-ai 主体一致）
- 独立路由 `/wenqu/*`，与通用聊天界面隔离
- 新增 API 模块：`src/lib/apis/wenqu/`

### 后端
- **Python FastAPI**（与 liya-ai 主体一致）
- 新增独立 Router：`routers/wenqu.py`（prefix: `/api/v1/wenqu`）
- 新增独立数据模型：`models/wenqu.py`
- 新增 Wenqu Engine：`utils/wenqu_engine/`
  - `resume_parser.py` — 简历解析
  - `project_selector.py` — 高价值项目识别
  - `question_engine.py` — 追问引擎（核心）
  - `feedback_engine.py` — 反馈报告生成

### 数据模型

```
wenqu_sessions        — 面试会话
wenqu_rounds          — 问答轮次
wenqu_feedback_reports — 反馈报告
```

### 依赖
- 共享 liya-ai 的 LLM 连接（Ollama / OpenAI 兼容 API）
- 共享用户认证系统
- 共享文件上传基础设施
- 共享数据库（SQLite / PostgreSQL）

---

## 6. 刻意不做（取舍）

- ❌ AI 语音输出（TTS）
- ❌ 视频面试
- ❌ 泛化求职八股
- ❌ 非计算机专业场景
- ❌ 花哨 UI
- ❌ 社交功能
- ❌ 排行榜
- ❌ 多用户复杂系统
- ✅ 保留：语音输入（ASR）、Markdown 报告、导师人格化 Prompt、高质量科研追问引擎

---

## 7. 核心 Prompt 设计

```python
SYSTEM_PROMPT = """
你是一位极其严格的计算机系博士生导师，
长期参与保研复试。

你会通过连续追问验证学生科研经历真实性。

重点考察：
- 原理理解
- 实验设计
- 技术选型
- Failure Analysis
- 改进能力
- 学术表达严谨度

禁止泛泛鼓励，必须持续施压。
"""
```

---

## 8. 与 liya-ai 主体的关系

| | liya-ai 主体 | 问渠模块 |
|---|---|---|
| 功能 | 通用 LLM 聊天 | 保研复试模拟面试 |
| 路由 | `/` | `/wenqu/*` |
| API | `/api/v1/chats/*` 等 | `/api/v1/wenqu/*` |
| 代码位置 | `src/routes/` | `src/routes/wenqu/` |
| 数据模型 | `models/chats.py` 等 | `models/wenqu.py` |
| 是否需要 Auth | 是 | 是（复用） |
| LLM 调用 | 复用 | 复用 |

问渠不修改任何 liya-ai 主体代码，所有改动均为**新增文件**。

---

## 9. 开发者

基于 [Open WebUI](https://github.com/open-webui/open-webui) fork 的 liya-ai 项目，新增问渠模块。

> 问渠模块为原创代码，与 Open WebUI 上游无关联。
