# MEMORY.md - Long-Term Memory

## Evan's Capabilities

### Web Search

| Provider | Status | Config |
|----------|--------|--------|
| **Brave API** | ✅ Active | Built-in web_search tool |
| **Tavily API** | ✅ Available | Requires TAVILY_API_KEY env var |
| **Codex Deep Search** | 🔄 Available | Requires Codex CLI installation |

### Codex Deep Search

| Status | Location |
|--------|----------|
| ✅ **已配置** | `/home/lenovo/.openclaw/workspace/skills/codex-deep-search/` |

**个性化配置完成 (2026-02-25):**
- 路径已个性化: `/home/lenovo/` (原 `/home/ubuntu/`)
- 结果目录: `/home/lenovo/.openclaw/workspace/data/codex-search-results/`
- 消息通道: WhatsApp (原 Telegram)
- 回调参数: `--whatsapp "+86手机号"`

**Usage:**
```bash
# Background search with WhatsApp callback
bash /home/lenovo/.openclaw/workspace/skills/codex-deep-search/scripts/search.sh \
  --prompt "query" \
  --task-name "task-name" \
  --whatsapp "[PHONE_REDACTED]"

# Sync search (no callback)
bash /home/lenovo/.openclaw/workspace/skills/codex-deep-search/scripts/search.sh \
  --prompt "query" \
  --output "/tmp/result.md" \
  --timeout 60
```

**参数说明:**
| Flag | Required | Description |
|------|----------|-------------|
| `--prompt` | ✅ | 研究查询 |
| `--output` | ❌ | 输出文件路径 |
| `--task-name` | ❌ | 任务标识符 |
| `--whatsapp` | ❌ | WhatsApp 回调目标 (手机号) |
| `--timeout` | ❌ | 超时秒数 (默认120) |

## CEO Preferences (Verified)

- CTO-level technical understanding
- Requires exhaustive detail on bugs/architecture
- Zero-trust verification mandate active
- BLUF communication for strategy
- Detailed technical explanations required

---

## GitHub Configuration (2026-02-28)

| Item | Value |
|------|-------|
| **Username** | DrPei12 |
| **Token** | [GITHUB_TOKEN_REDACTED] |
| **Default Repo** | https://github.com/DrPei12/errorpare |

**Token stored in:** `~/.openclaw/workspace/GITHUB_CONFIG.md`

*Last Updated: 2026-02-28*

---

## ErrorPare Phase 2.1 完成 (2026-03-03)

### 已交付功能

| 模块 | 状态 | 说明 |
|------|------|------|
| **配置系统** | ✅ | `~/.errorpare/config.json` 持久化配置 |
| **配置向导** | ✅ | `errorpare init` 交互式配置 |
| **规则引擎** | ✅ | 50+ 错误模式规则 (TS/Python/Java/Go/Rust) |
| **LLM 分析器** | ✅ | 5 供应商支持 (OpenAI/Anthropic/百炼/Moonshot/DeepSeek) |
| **智能压缩** | ✅ | 第三方帧折叠 + 错误去重分组 |
| **Postinstall** | ✅ | npm 安装后自动引导配置 |

### npm 发布

| 版本 | 日期 | 状态 |
|------|------|------|
| v2.0.0 | 2026-03-03 | ✅ 已发布 |
| v2.0.1 | 2026-03-03 | ✅ 已发布 (postinstall 修复) |

### 使用方式

```bash
npm install -g errorpare
errorpare init --analyze --provider deepseek
errorpare run "npm run build" --analyze
```

*Last Updated: 2026-03-03*
