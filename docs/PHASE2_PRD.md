# SecondBrain Phase 2 产品需求文档 (PRD)

**文档版本**: v1.0  
**创建日期**: 2026-03-06  
**作者**: Evan (CAOO)  
**项目状态**: Phase 1 完成 → Phase 2 规划中  
**评审状态**: 待评审

---

## 文档修订历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-03-06 | Evan | 初始版本，覆盖 Phase 2 完整生命周期 |

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [产品愿景与定位](#2-产品愿景与定位)
3. [目标用户与市场](#3-目标用户与市场)
4. [竞争分析](#4-竞争分析)
5. [Phase 2 功能需求](#5-phase-2-功能需求)
6. [技术架构设计](#6-技术架构设计)
7. [部署策略](#7-部署策略)
8. [开发路线图](#8-开发路线图)
9. [测试与验收标准](#9-测试与验收标准)
10. [风险与缓解](#10-风险与缓解)
11. [成功指标](#11-成功指标)
12. [Phase 3 展望](#12-phase-3-展望)

---

## 1. 执行摘要

### 1.1 项目背景

SecondBrain 项目 Phase 1 已完成基础功能开发，实现了：
- Next.js + FastAPI 全栈架构
- 笔记管理（CRUD + 状态流转）
- LightRAG 集成（语义检索 + Q&A）
- 基础 API 接口（供 AI Agent 调用）

### 1.2 Phase 2 核心目标

**战略调整**: 基于市场调研，Phase 2 将聚焦于**个人开发者**市场，采用**本地优先、云端演进**的策略。

**核心目标**:
1. 完善本地部署体验，降低个人开发者使用门槛
2. 开发 CLI 工具，实现命令行快速上传/检索
3. 深度集成主流 AI Agent（Claude Code/Codex/OpenClaw）
4. 验证 RAG 效果与延迟，积累真实使用数据
5. 为未来云端 SaaS 化奠定技术基础

### 1.3 关键决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **目标用户** | 个人开发者 | 市场空白，付费意愿强，易于触达 |
| **部署方式** | 本地优先 | 零成本启动，数据隐私，快速验证 |
| **云端策略** | 延迟决策 | 待本地验证效果后再评估 |
| **集成重点** | Claude Code + Codex | 当前最流行的 AI 编程助手 |

### 1.4 时间线与资源

- **开发周期**: 8 周 (2026-03-10 ~ 2026-05-05)
- **核心团队**: 1 名全栈开发者 (CEO) + Evan (CAOO) 支持
- **基础设施**: 本地开发环境，无需购置服务器
- **预算**: $0 (Phase 2 本地测试阶段)

---

## 2. 产品愿景与定位

### 2.1 产品愿景

**让每位开发者拥有 AI 增强的第二大脑**

在 AI Agent 成为标配开发工具的时代，SecondBrain 致力于成为开发者的"外部记忆皮层"——自动记录、智能组织、随时检索，让 AI Agent 理解你的项目、你的决策、你的知识脉络。

### 2.2 产品定位

| 维度 | 定位描述 |
|------|----------|
| **目标用户** | 个人开发者、独立开发者、技术创业者 |
| **使用场景** | 与 AI Agent 协作开发过程中的知识管理 |
| **核心价值** | 让 AI Agent 拥有长期记忆，理解上下文 |
| **差异化** | 本地优先、CLI-first、Agent 原生集成 |
| **商业模式** | Phase 2 免费本地使用 → Phase 3 云端 SaaS |

### 2.3 产品原则

1. **本地优先 (Local-First)**: 数据存储在用户本地，隐私可控
2. **CLI-First**: 命令行优先，适配开发者工作流
3. **Agent-Native**: 为 AI Agent 设计，而非人类 UI
4. **渐进增强**: 从本地到云端，平滑演进
5. **零配置启动**: 5 分钟内完成安装并开始使用

### 2.4 不做的事情

| 不做 | 理由 |
|------|------|
| ❌ 企业级权限管理 | 个人用户不需要 |
| ❌ 复杂可视化编排 | 增加复杂度，偏离核心场景 |
| ❌ 多租户 SaaS (Phase 2) | 待本地验证后再投入 |
| ❌ 移动端 App | 开发者主要在桌面工作 |
| ❌ 自建向量数据库 | 使用成熟方案 (ChromaDB/PGVector) |

---

## 3. 目标用户与市场

### 3.1 目标用户画像

#### 主要用户：独立开发者 Alex

| 属性 | 描述 |
|------|------|
| **年龄** | 28-35 岁 |
| **职业** | 独立开发者/技术创业者 |
| **技术栈** | TypeScript/Python/Go |
| **AI 工具** | Claude Code (每日使用), Codex, Cursor |
| **痛点** | AI Agent 记不住项目上下文，每天重复解释 |
| **付费意愿** | $10-20/月 (已习惯 Cursor/Copilot 付费) |
| **获取渠道** | GitHub, Twitter/X, 技术博客，Product Hunt |

**典型一天**:
```
09:00 - 用 Claude Code 继续昨天的功能开发
        → Claude 不记得昨天的讨论，需要重新解释
        → 浪费时间，体验断裂
        
14:00 - 阅读一篇技术文章，想保存供以后参考
        → 收藏到浏览器，但再也不会看
        
20:00 - 想让 AI 帮忙总结本周的工作进展
        → 需要手动整理聊天记录和代码变更
        → 太麻烦，放弃
```

**SecondBrain 解决方案**:
```
09:00 - Claude Code 自动从 SecondBrain 检索昨天上下文
        → 无缝继续，效率提升
        
14:00 - `sb save article.pdf --tags "architecture,rust"`
        → 自动索引，可语义检索
        
20:00 - `sb summary --week`
        → AI 自动生成周报，包含所有笔记和代码变更
```

### 3.2 市场规模估算

| 指标 | 数值 | 来源 |
|------|------|------|
| **全球独立开发者** | ~500 万 | GitHub 2025 报告 |
| **AI 工具付费用户** | ~200 万 | Cursor/Copilot 用户数推算 |
| **目标渗透率** | 1-2% | 早期采用者 |
| **潜在付费用户** | 2-4 万 | 可触达市场 |
| **ARPU** | $10/月 | 个人定价 |
| **潜在 MRR** | $20-40 万/月 | 成熟期估算 |

### 3.3 用户需求层次

```
Level 4: 自动化洞察 (Phase 4)
         └─ "AI 主动告诉我遗漏的重要信息"
         
Level 3: 云端同步 (Phase 3)
         └─ "多设备无缝访问我的知识库"
         
Level 2: Agent 集成 (Phase 2)
         └─ "Claude Code 自动检索我的笔记"
         
Level 1: 基础存储 (Phase 1 ✅)
         └─ "我能上传和检索文档"
```

---

## 4. 竞争分析

### 4.1 竞争格局总览

| 竞争者 | 类型 | 目标用户 | 定价 | 优势 | 劣势 |
|--------|------|----------|------|------|------|
| **Dify.AI** | RaaS 平台 | 开发者/企业 | $50+/月 | 功能完整 | 复杂，不适合个人 |
| **LlamaCloud** | RaaS 平台 | 企业 | 定制 | LlamaIndex 官方 | 企业级，价格高 |
| **Pinecone** | 向量 DB + RAG | 开发者 | $25+/月 | 品牌知名 | 需要自行集成 |
| **Khoj** | 开源第二大脑 | 技术爱好者 | 免费 | 开源免费 | 需自托管，Agent 集成弱 |
| **Quivr** | 开源第二大脑 | 开发者 | 免费 + 企业版 | 功能多 | 定位模糊 |
| **SecondBrain** | 个人开发者工具 | 个人开发者 | 免费 (Phase 2) | 本地优先，CLI-first，Agent 原生 | 新功能，无品牌 |

### 4.2 差异化策略

**SecondBrain 的护城河**:

1. **本地优先架构**: 数据在用户手中，隐私无忧
2. **CLI-First 设计**: 符合开发者习惯，无需学习新 UI
3. **深度 Agent 集成**: 不是"支持 API"，而是"原生集成"
4. **渐进式演进**: 从本地到云端，用户数据可迁移
5. **开源社区**: 核心功能开源，建立开发者信任

### 4.3 竞争响应策略

| 竞争动作 | 我们的响应 |
|----------|------------|
| Dify 推出个人版 | 强调本地部署优势 + CLI 体验 |
| Khoj 改进 Agent 集成 | 加速 Claude Code/Codex 深度集成 |
| 大厂进入个人市场 | 强调开源 + 数据可迁移性 |

---

## 5. Phase 2 功能需求

### 5.1 功能总览

| 模块 | 功能 | 优先级 | 工期 |
|------|------|--------|------|
| **CLI 工具** | `sb upload` / `sb search` / `sb connect` | P0 | 2 周 |
| **用户系统** | 本地用户配置 + API Key 管理 | P0 | 1 周 |
| **Agent 集成** | Claude Code MCP + Codex Skill | P0 | 2 周 |
| **RAG 优化** | 检索质量提升 + 延迟优化 | P1 | 2 周 |
| **批量导入** | 文件夹/URL 批量导入 | P1 | 1 周 |
| **使用统计** | 本地用量统计 | P2 | 3 天 |

### 5.2 详细功能需求

#### 5.2.1 CLI 工具 (sb-cli)

**用户故事**:
```
作为一个开发者
我希望通过命令行快速上传和检索知识
以便无缝集成到我的开发工作流中
```

**功能需求**:

| 命令 | 描述 | 示例 |
|------|------|------|
| `sb init` | 初始化配置 | `sb init --provider openai` |
| `sb upload <path>` | 上传文件/文件夹 | `sb upload ./docs --tags "api,design"` |
| `sb search <query>` | 语义检索 | `sb search "认证流程" --top 5` |
| `sb connect <agent>` | 连接 AI Agent | `sb connect claude-code` |
| `sb status` | 查看状态 | `sb status` |
| `sb export` | 导出数据 | `sb export --format markdown` |

**技术需求**:
- Python 实现 (typer/click)
- 支持 Windows/macOS/Linux
- 发布到 PyPI (`pip install sb-cli`)
- 自动更新检查

**验收标准**:
- [ ] `sb --help` 显示完整帮助
- [ ] 上传 100MB 文件 < 10 秒
- [ ] 检索响应 < 2 秒
- [ ] 支持中文查询

---

#### 5.2.2 用户系统 (本地)

**用户故事**:
```
作为一个用户
我希望管理我的配置和 API Key
以便安全地使用 SecondBrain
```

**功能需求**:

| 功能 | 描述 |
|------|------|
| **本地配置** | `~/.secondbrain/config.yaml` 存储配置 |
| **API Key 管理** | 生成/撤销本地 API Key |
| **多配置支持** | 支持多套配置 (工作/个人) |
| **环境变量** | 支持 `.env` 文件配置 |

**配置示例**:
```yaml
# ~/.secondbrain/config.yaml
profile: default
data_dir: ~/.secondbrain/data

llm:
  provider: openai
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}

embedding:
  model: text-embedding-3-small

rag:
  top_k: 5
  threshold: 0.7
```

**验收标准**:
- [ ] `sb init` 创建配置文件
- [ ] 支持环境变量引用
- [ ] 配置验证与错误提示

---

#### 5.2.3 Agent 集成

**Claude Code MCP Server**:

**用户故事**:
```
作为一个 Claude Code 用户
我希望 Claude 自动检索我的 SecondBrain
以便理解我的项目上下文
```

**技术实现**:
```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "secondbrain": {
      "command": "sb-mcp",
      "args": ["--config", "~/.secondbrain/config.yaml"]
    }
  }
}
```

**MCP Tools**:
- `search_knowledge(query, top_k)` - 检索知识
- `upload_document(path, tags)` - 上传文档
- `list_recent(limit)` - 最近笔记

**Codex OpenClaw Skill**:

**用户故事**:
```
作为一个 Codex 用户
我希望 Codex 能访问我的 SecondBrain
以便获得项目上下文
```

**技术实现**:
```javascript
// OpenClaw skill 配置
{
  "name": "secondbrain",
  "description": "Query SecondBrain knowledge base",
  "endpoint": "http://localhost:8000/api/rag/query",
  "auth": "api_key"
}
```

**验收标准**:
- [ ] Claude Code 可调用 MCP 工具
- [ ] Codex 可通过 OpenClaw 检索
- [ ] 检索结果自动注入上下文

---

#### 5.2.4 RAG 优化

**当前问题**:
- 检索准确率不稳定
- 长文档检索效果差
- 延迟较高 (3-5 秒)

**优化目标**:
- 检索准确率 > 85%
- 延迟 < 2 秒
- 支持长文档 (100+ 页)

**技术方案**:

| 优化项 | 方案 | 预期效果 |
|--------|------|----------|
| **分块策略** | 语义分块 + 重叠 | 提升上下文完整性 |
| **混合检索** | BM25 + 向量 | 提升召回率 |
| **重排序** | Cross-Encoder Rerank | 提升 Top-K 质量 |
| **缓存** | Redis/本地缓存 | 降低延迟 |
| **批处理** | 批量 Embedding | 提升吞吐量 |

**验收标准**:
- [ ] 标准测试集准确率 > 85%
- [ ] P95 延迟 < 2 秒
- [ ] 支持 100+ 页 PDF

---

#### 5.2.5 批量导入

**用户故事**:
```
作为一个用户
我希望批量导入文件夹或 URL
以便快速建立知识库
```

**功能需求**:

| 导入源 | 支持格式 | 处理方式 |
|--------|----------|----------|
| **本地文件夹** | PDF/MD/TXT/DOCX | 递归扫描 + 自动索引 |
| **URL** | 网页 | 爬取 + 内容提取 |
| **GitHub Repo** | 代码仓库 | 克隆 + 索引代码文档 |
| **Notion** | Notion 页面 | API 导入 (Phase 2.5) |

**CLI 示例**:
```bash
# 导入文件夹
sb upload ./docs --recursive --tags "project,docs"

# 导入 URL
sb upload https://example.com/article --type url

# 导入 GitHub 仓库
sb upload https://github.com/user/repo --type github
```

**验收标准**:
- [ ] 支持 1000+ 文件批量导入
- [ ] 断点续传支持
- [ ] 导入进度显示

---

#### 5.2.6 使用统计

**用户故事**:
```
作为一个用户
我希望了解我的使用情况
以便评估价值
```

**统计指标**:

| 指标 | 描述 |
|------|------|
| **文档数量** | 总文档数/总大小 |
| **检索次数** | 每日/每周检索次数 |
| **热门查询** | 最常查询的关键词 |
| **Agent 调用** | Claude/Codex 调用次数 |

**CLI 示例**:
```bash
$ sb stats

📊 SecondBrain Usage Stats

Documents: 156 (245 MB)
Retrievals: 42 (this week)
Top queries: "API design", "auth flow", "database schema"
Agent calls: Claude Code (28), Codex (14)
```

**验收标准**:
- [ ] `sb stats` 显示统计
- [ ] 支持导出 JSON/CSV

---

## 6. 技术架构设计

### 6.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Local Machine                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CLI Tool   │  │  MCP Server  │  │  Web UI      │          │
│  │   (sb-cli)   │  │  (sb-mcp)    │  │  (Next.js)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Backend                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ Notes API    │  │ RAG API      │  │ Admin API    │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Data Layer                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │ SQLite       │  │ ChromaDB     │  │ File Storage │     │ │
│  │  │ (Metadata)   │  │ (Vectors)    │  │ (Documents)  │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 技术栈选型

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| **CLI** | Python + typer | 与后端技术栈一致，开发效率高 |
| **MCP Server** | Python + MCP SDK | Anthropic 官方支持 |
| **Backend** | FastAPI | 已有基础，性能好 |
| **Frontend** | Next.js 14 | 已有基础，SSR 支持 |
| **关系数据库** | SQLite (dev) → PostgreSQL (prod) | 轻量 → 生产 |
| **向量数据库** | ChromaDB (local) → Qdrant (cloud) | 本地简单 → 云端扩展 |
| **Embedding** | OpenAI text-embedding-3-small | 性价比高 |
| **LLM** | 用户自选 (OpenAI/Anthropic/本地) | 灵活性 |

### 6.3 数据模型

```python
# 核心数据模型

class User(Base):
    id: UUID
    email: str
    created_at: datetime
    config: JSON  # 用户配置

class Document(Base):
    id: UUID
    user_id: UUID
    title: str
    content: Text
    file_path: str
    file_size: int
    mime_type: str
    tags: List[str]
    metadata: JSON
    created_at: datetime
    updated_at: datetime
    indexed: bool  # RAG 索引状态

class Chunk(Base):
    id: UUID
    document_id: UUID
    content: Text
    embedding: Vector  # ChromaDB 存储
    chunk_index: int
    metadata: JSON

class RetrievalLog(Base):
    id: UUID
    user_id: UUID
    query: str
    results: List[UUID]
    latency_ms: int
    created_at: datetime
```

### 6.4 API 设计

**核心 API 端点**:

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/api/notes` | POST | 创建笔记 | API Key |
| `/api/notes` | GET | 列表笔记 | API Key |
| `/api/notes/{id}` | GET | 获取详情 | API Key |
| `/api/notes/{id}` | PUT | 更新笔记 | API Key |
| `/api/notes/{id}` | DELETE | 删除笔记 | API Key |
| `/api/rag/query` | POST | RAG 检索 | API Key |
| `/api/rag/index` | POST | 手动索引 | API Key |
| `/api/stats` | GET | 使用统计 | API Key |

**API 响应示例**:
```json
// POST /api/rag/query
{
  "query": "认证流程如何实现",
  "top_k": 5,
  "filter": {"tags": ["api", "security"]}
}

// Response
{
  "query": "认证流程如何实现",
  "results": [
    {
      "document_id": "uuid",
      "title": "API 认证设计文档",
      "content": "JWT + Refresh Token...",
      "score": 0.92,
      "tags": ["api", "security"]
    }
  ],
  "latency_ms": 245
}
```

---

## 7. 部署策略

### 7.1 Phase 2: 本地部署

**目标**: 零成本启动，快速验证

**部署方式**:
```bash
# 一键安装脚本
curl -fsSL https://secondbrain.dev/install.sh | bash

# 或手动安装
git clone https://github.com/DrPei12/secondbrain.git
cd secondbrain
./install.sh

# 启动服务
sb start

# 验证
sb status
```

**系统要求**:
- macOS 12+ / Windows 11 / Linux (Ubuntu 20.04+)
- Python 3.10+
- Node.js 18+
- 4GB+ RAM
- 10GB+ 磁盘空间

**数据存储**:
```
~/.secondbrain/
├── config.yaml      # 用户配置
├── data/
│   ├── documents/   # 原始文档
│   ├── sqlite.db    # 元数据
│   └── chroma/      # 向量索引
└── logs/
    └── app.log
```

### 7.2 Phase 3: 云端演进 (规划)

**触发条件**:
- 本地用户 > 1000
- 付费意愿验证 (>10% 转化率)
- 云端需求明确 (多设备同步需求)

**云端架构**:
```
┌─────────────────────────────────────────────────────────────────┐
│                         Cloud Infrastructure                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Load       │  │   API        │  │   Auth       │          │
│  │   Balancer   │  │   Gateway    │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                    │
│         ▼                 ▼                 ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   App        │  │   RAG        │  │   Worker     │          │
│  │   Servers    │  │   Service    │  │   (Embedding)│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                    │
│         ▼                 ▼                 ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │ Qdrant Cloud │  │ S3 Storage   │          │
│  │ (Supabase)   │  │ (Vectors)    │  │ (Documents)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**云端成本估算** (1000 用户):
| 服务 | 月成本 |
|------|--------|
| Supabase (PostgreSQL) | $25 |
| Qdrant Cloud | $50 |
| S3 Storage | $10 |
| Compute (Render/Railway) | $50 |
| **总计** | **$135/月** |

**云端定价建议**:
- Free: $0/月 (100 文档，1GB 存储)
- Pro: $9/月 (1000 文档，10GB 存储)
- Team: $29/月 (10000 文档，100GB 存储)

---

## 8. 开发路线图

### 8.1 总体时间线

```
Week 1-2  (03/10-03/23): CLI 工具 + 用户系统
Week 3-4  (03/24-04/06): Agent 集成 (Claude Code + Codex)
Week 5-6  (04/07-04/20): RAG 优化 + 批量导入
Week 7-8  (04/21-05/05): 测试 + 文档 + 发布
```

### 8.2 详细里程碑

#### Milestone 1: CLI 工具 (Week 1-2)

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|----------|
| CLI 框架搭建 | CEO | `sb-cli` 基础命令 | `sb --help` 可用 |
| `sb upload` 实现 | CEO | 文件上传功能 | 支持单文件/文件夹 |
| `sb search` 实现 | CEO | 语义检索功能 | 响应 < 2 秒 |
| `sb init` 实现 | CEO | 配置初始化 | 创建配置文件 |
| PyPI 发布 | CEO | `pip install sb-cli` | 可安装 |

#### Milestone 2: Agent 集成 (Week 3-4)

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|----------|
| MCP Server 开发 | CEO | `sb-mcp` | Claude Code 可调用 |
| Claude Code 集成 | CEO | `.claude/settings.json` 示例 | 自动检索 |
| OpenClaw Skill | CEO | secondbrain skill | Codex 可调用 |
| 集成测试 | CEO | 测试用例 | 端到端测试通过 |

#### Milestone 3: RAG 优化 (Week 5-6)

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|----------|
| 混合检索实现 | CEO | BM25 + 向量 | 召回率提升 |
| Rerank 集成 | CEO | Cross-Encoder | Top-K 质量提升 |
| 缓存层实现 | CEO | Redis/本地缓存 | 延迟降低 50% |
| 批量导入 | CEO | `sb upload --recursive` | 1000+ 文件 |

#### Milestone 4: 发布准备 (Week 7-8)

| 任务 | 负责人 | 交付物 | 验收标准 |
|------|--------|--------|----------|
| 文档编写 | CEO | README + 使用指南 | 完整清晰 |
| 测试修复 | CEO | Bug 修复 | 无 P0/P1 Bug |
| 发布脚本 | CEO | `install.sh` | 一键安装 |
| 发布宣传 | CEO | GitHub + Twitter | 发布帖子 |

### 8.3 每日站会模板

```markdown
## Daily Standup - YYYY-MM-DD

### Yesterday
- [完成的任务]

### Today
- [计划任务]

### Blockers
- [阻碍/需要帮助]

### Metrics
- Documents indexed: X
- Avg retrieval latency: X ms
- Bugs open: X
```

---

## 9. 测试与验收标准

### 9.1 测试策略

| 测试类型 | 工具 | 覆盖率目标 |
|----------|------|------------|
| **单元测试** | pytest + vitest | 80%+ |
| **集成测试** | pytest + httpx | 核心流程 100% |
| **E2E 测试** | Playwright | 关键用户流程 |
| **性能测试** | locust | P95 延迟 < 2 秒 |
| **负载测试** | locust | 100 并发用户 |

### 9.2 验收标准

#### CLI 工具验收

| 测试项 | 预期结果 |
|--------|----------|
| `sb --help` | 显示完整帮助信息 |
| `sb init` | 创建配置文件，无错误 |
| `sb upload file.pdf` | 上传成功，显示进度 |
| `sb search "query"` | 返回相关结果，< 2 秒 |
| `sb connect claude-code` | 创建 MCP 配置 |

#### Agent 集成验收

| 测试项 | 预期结果 |
|--------|----------|
| Claude Code MCP 连接 | 工具列表显示 secondbrain |
| Claude 检索测试 | 返回 SecondBrain 内容 |
| Codex OpenClaw 调用 | API 响应正常 |

#### RAG 性能验收

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 检索准确率 | > 85% | 标准测试集 |
| P50 延迟 | < 1 秒 | locust |
| P95 延迟 | < 2 秒 | locust |
| 吞吐量 | > 10 req/s | locust |

### 9.3 发布清单

- [ ] 所有 P0/P1 Bug 修复
- [ ] 单元测试覆盖率 > 80%
- [ ] 文档完整 (README + API + CLI)
- [ ] 安装脚本测试通过
- [ ] 示例项目准备
- [ ] GitHub Release 创建
- [ ] PyPI 包发布
- [ ] 发布宣传材料

---

## 10. 风险与缓解

### 10.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| RAG 效果不达预期 | 高 | 中 | 预留 2 周优化时间，准备降级方案 |
| Agent 集成兼容性问题 | 中 | 中 | 多版本测试，提供回退方案 |
| 性能瓶颈 (大文档) | 中 | 高 | 分块策略优化，增量索引 |
| 跨平台兼容性问题 | 中 | 中 | CI/CD 多平台测试 |

### 10.2 产品风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 用户需求不匹配 | 高 | 中 | 早期用户访谈，快速迭代 |
| 付费意愿低 | 高 | 中 | Phase 2 免费验证，Phase 3 再商业化 |
| 竞争加剧 | 中 | 高 | 差异化定位，加速开发 |

### 10.3 执行风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 开发延期 | 中 | 中 | 优先级管理，MVP 优先 |
| CEO 时间不足 | 高 | 中 | Evan 分担开发，简化范围 |
| 技术债务积累 | 中 | 高 | 每周代码审查，重构时间 |

### 10.4 风险应对预案

**预案 A: RAG 效果持续不佳**
- 降级到关键词检索
- 引入人工标注优化
- 考虑切换 RAG 框架

**预案 B: Agent 集成受阻**
- 优先保证 CLI 可用
- 提供 Webhook 替代方案
- 等待官方 API 更新

**预案 C: 用户需求不匹配**
- 暂停开发，深度访谈
- Pivot 到相邻场景
- 开源项目，社区驱动

---

## 11. 成功指标

### 11.1 Phase 2 成功标准

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| **GitHub Stars** | 100+ | GitHub API |
| **CLI 下载量** | 500+ | PyPI stats |
| **活跃用户** | 50+ (周活) | 本地统计上报 (可选) |
| **用户反馈** | 10+ 深度反馈 | GitHub Issues/Discussions |
| **Agent 集成使用率** | > 60% | 使用统计 |

### 11.2 技术指标

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| **检索准确率** | > 85% | 标准测试集 |
| **P95 延迟** | < 2 秒 | locust |
| **系统可用性** | > 99% | 本地运行时间 |
| **Bug 密度** | < 1/1000 行 | 测试报告 |

### 11.3 用户满意度

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| **NPS** | > 30 | 用户调研 |
| **推荐意愿** | > 70% | 用户调研 |
| **留存率 (周)** | > 50% | 使用统计 |

---

## 12. Phase 3 展望

### 12.1 Phase 3 目标 (云端 SaaS)

**触发条件**:
- Phase 2 用户 > 1000
- 付费意愿验证 (>10% 转化率)
- 多设备同步需求明确

**核心功能**:
- 云端存储与同步
- 多设备访问
- 团队协作
- 付费系统

### 12.2 长期愿景

```
Phase 1 (✅): 基础功能 - 本地笔记 + RAG
Phase 2 (🔄): Agent 集成 - CLI + MCP + Skill
Phase 3 (📅): 云端 SaaS - 多设备同步 + 付费
Phase 4 (🔮): AI 洞察 - 主动推荐 + 知识图谱
```

### 12.3 退出策略

**如果 Phase 2 未达预期**:
1. 开源项目，社区维护
2. 技术复用 (RAG 能力集成到其他产品)
3.  Pivot 到企业市场

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **RAG** | Retrieval-Augmented Generation，检索增强生成 |
| **MCP** | Model Context Protocol，Anthropic 的模型上下文协议 |
| **CLI** | Command Line Interface，命令行界面 |
| **SaaS** | Software as a Service，软件即服务 |
| **ARPU** | Average Revenue Per User，每用户平均收入 |

### B. 参考资源

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### C. 联系方式

- **GitHub**: https://github.com/DrPei12/secondbrain
- **Email**: contact@secondbrain.dev (待注册)
- **Twitter**: @secondbrain_dev (待注册)

---

**文档结束**

*Last Updated: 2026-03-06*
