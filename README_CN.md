# Second Brain - 个人知识管理平台

[English](README_EN.md) | [简体中文](README_CN.md)

Second Brain 是一个轻量级个人知识管理 Web 应用，基于 Next.js 和 FastAPI 构建。它帮助用户捕捉笔记、审核归档、打标签，并通过 RAG 问答界面检索自己的个人知识库。

## 技术栈

- **前端**：Next.js App Router、Tailwind CSS、Shadcn/ui 风格组件
- **后端**：Python FastAPI
- **数据库**：开发环境 SQLite，生产环境架构可迁移到 PostgreSQL
- **RAG**：来自 RAG-Anything 的 LightRAG
- **API 风格**：面向笔记和知识库查询的 REST 接口

## 项目结构

```text
SecondBrain/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── notes.py
│   │   │       ├── rag.py
│   │   │       └── health.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
└── README.md
```

## 功能特性

### 核心知识工作流

- 创建、读取、更新、删除 Markdown 笔记。
- 支持 `Inbox -> Reviewed -> Archived` 状态流转。
- 使用标签组织笔记。
- 记录知识来源，保留原始上下文。

### AI 功能

- 集成 LightRAG 作为 RAG 能力。
- 支持对个人知识库进行自然语言问答。
- 支持 AI 生成笔记摘要。

### API 接口

后端提供面向外部 AI Agent 和前端工作流的 REST 接口：

- `POST /api/notes`：创建单条或批量笔记
- `GET /api/notes`：按筛选条件列出笔记
- `GET /api/notes/{id}`：获取笔记详情
- `PUT /api/notes/{id}`：更新笔记
- `DELETE /api/notes/{id}`：删除笔记
- `POST /api/rag/query`：发起 RAG 问答
- `POST /api/rag/index`：为笔记建立 RAG 索引

## 快速开始

### 后端启动

```bash
cd backend
cp .env.example .env

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Windows PowerShell 中可用以下命令激活虚拟环境：

```powershell
.\venv\Scripts\Activate.ps1
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 根目录快捷命令

```bash
npm run dev
npm run install:all
```

## 开发说明

- 保持笔记 CRUD 与 RAG 索引解耦，避免模型或 embedding 服务不可用时影响基础记录能力。
- 保持来源追踪清晰；个人知识库的长期价值取决于是否能回溯原始来源。
- 将 API 视为后续 Agent、导入器和自动化工具的集成表面。

## 许可证

MIT License。

