<div align="center">

**English** · [Русский](README.ru.md)

# BWA

**A Telegram assistant with web search and conversation memory**

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![aiogram 3.31](https://img.shields.io/badge/aiogram-3.31-2CA5E0?logo=telegram&logoColor=white)
![LangGraph 1.2](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)
![MCP](https://img.shields.io/badge/MCP-tools-8A2BE2)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

Search the web, read sources, and continue conversations directly in Telegram.
Built with aiogram, LangGraph, and MCP tools backed by SearXNG.

[Features](#features) · [Quick start](#quick-start) · [Configuration](#configuration) · [Usage](#usage)

</div>

---

## Features

| Feature | Description |
| --- | --- |
| 🔎 **Web search** | Search, query suggestions, and page reading through MCP tools |
| 🧠 **Conversation memory** | SQLite checkpoints and reply-based conversation branches |
| 📝 **Rich Markdown** | Native Telegram Rich Messages with lists, tables, links, and code |
| 🎭 **Custom modes** | Commands, descriptions, and assistant prompts configured in YAML |
| 🧾 **Optional history** | An expandable summary of messages, tool calls, and tool results |
| 🌐 **Separate proxies** | Independent proxy settings for the LLM, Telegram, and search traffic |
| 🐳 **Docker Compose** | Bot, SearXNG, and the MCP search server on one private Docker network |

## Quick start

You need Docker Compose, a Telegram bot token, and an OpenAI-compatible
Chat Completions API supporting tool calls and `tool_choice="required"`.

1. Copy [`.env.example`](.env.example) to `.env`.
2. Set your bot and model credentials:

   ```dotenv
   BOT_TOKEN=your-telegram-bot-token
   API_BASE=https://your-provider.example/v1
   API_KEY=your-api-key
   MODEL=your-model-id
   MCP_SERVERS={"searxng":{"url":"http://mcp-search:3000/mcp"}}
   LOG_LEVEL=INFO
   CHECK_HISTORY=false
   ```

3. Review [`searxng/settings.yml`](searxng/settings.yml): set a unique
   `server.secret_key` and configure or remove `outgoing.proxies` for your
   environment. Keep `json` enabled in `search.formats`.
4. Start the stack:

   ```bash
   docker compose up -d --build
   ```

Send `/clear How do hummingbirds hover?` to the bot.

The bot uses long polling; no public webhook endpoint is needed. Compose mounts
`./data` for conversation storage and `./searxng` for search configuration.

## Usage

| Action | Example |
| --- | --- |
| Start a conversation | `/clear How do solar panels work?` |
| Continue a conversation | Reply to the bot with `/clear What about cloudy weather?` |
| Ask about a text message | Reply to that message with `/clear` |

Only configured commands are handled. A command that does not reply to a linked
bot message starts a new conversation. When replying to the bot, include your
new question: Rich Messages may not provide a plain `text` field.

### Custom modes

The included mode is `/clear`, a general assistant. Add modes in
[`docs/prompts.yml`](docs/prompts.yml); each entry becomes a Telegram command:

```yaml
modes:
  clear:
    description: General assistant
    prompt: |-
      You are a helpful assistant.

  tutor:
    description: Explain concepts step by step
    prompt: |-
      Explain concepts using clear examples and short steps.
```

Restart the bot after editing prompts. Shared search rules from
[`app/core/prompts.py`](app/core/prompts.py) apply to every mode.
The bundled prompts and some Telegram interface strings are currently in Russian.

## Configuration

| Variable | Required | Default | Purpose |
| --- | :---: | --- | --- |
| `BOT_TOKEN` | yes | — | Telegram bot token |
| `API_BASE` | yes | — | Provider base URL, without `/chat/completions` |
| `API_KEY` | for API access | — | Provider API key; use `unused` for a local API without authentication |
| `MODEL` | yes | — | Exact model identifier accepted by the provider |
| `MCP_SERVERS` | yes | `{}` | MCP server configuration as JSON; startup requires at least one tool |
| `PROXY` | no | — | Proxy for LLM requests |
| `TG_PROXY` | no | — | Proxy for Telegram Bot API requests |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `CHECK_HISTORY` | no | `false` | Include a conversation and tool history summary before the answer |

Leave unused proxies commented out or empty. `PROXY` and `TG_PROXY` do not route
SearXNG traffic: configure its proxy separately through `outgoing.proxies` in
[`searxng/settings.yml`](searxng/settings.yml).

### Search services

| Service | Role |
| --- | --- |
| `bwa` | Telegram updates, model calls, and graph execution |
| `mcp-search` | MCP interface for search and page-reading tools |
| `searxng` | Queries to external search engines |

The bundled MCP server provides `searxng_web_search`,
`searxng_search_suggestions`, `searxng_instance_info`, and `web_url_read`.
The actual tool list is discovered at startup.

Every request starts with a neutral `search` node using `tool_choice="required"`.
After tool execution, `assistant` uses the selected mode and `tool_choice="auto"`
to request more tools or return an answer. `required` demands a tool call, but
does not select a specific search tool or guarantee successful results. A provider
response without the required call produces a warning; the graph continues.

Missing tools, duplicate tool names, or failure to connect to a configured MCP
server prevent startup. The search services have no published host ports in the
included Compose configuration.

## Storage

| File | Contents |
| --- | --- |
| `data/checkpoints.sqlite3` | Conversation state, including tool calls and results |
| `data/links.sqlite3` | Links between Telegram messages, conversations, and checkpoints |

Replying to an earlier bot message resumes its checkpoint, allowing separate
conversation branches. The data directory persists across container recreation.

With `CHECK_HISTORY=true`, the answer includes an expandable history summary.
Long entries are shortened and older entries may be hidden. The current final
answer is displayed separately, without duplication in the summary.

## Local development

Use Python 3.13 and an MCP server reachable from your host. The Compose address
`http://mcp-search:3000/mcp` resolves inside the Docker network only.

<details>
<summary>Linux / macOS</summary>

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
mkdir -p data
# Edit .env and set a host-reachable MCP_SERVERS URL.
python main.py
```

</details>

<details>
<summary>Windows PowerShell</summary>

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
New-Item -ItemType Directory -Force data
# Edit .env and set a host-reachable MCP_SERVERS URL.
.\.venv\Scripts\python.exe main.py
```

</details>

Run commands from the project root: `.env` and SQLite paths are relative to it.

## Operations and troubleshooting

```bash
# Recent logs from all services
docker compose logs --since=15m --tail=100 bwa searxng mcp-search

# Follow bot logs
docker compose logs -f bwa

# Stop the stack
docker compose down
```

`INFO` records request progress, model decisions, and tool outcomes using standard
Loguru formatting. `DEBUG` adds token usage, checkpoints, and error tracebacks.
Use the conversation identifier to follow related log messages.

<details>
<summary>Search returns CAPTCHA or times out</summary>

Check the `searxng` and `mcp-search` logs and outbound connectivity from the
SearXNG container. A CAPTCHA or blocked IP is not fixed by increasing timeouts.
LLM and Telegram proxy settings do not apply to the search container.

For DuckDuckGo, `CAPTCHA (wt-wt)` may be related to the `all` language setting;
see [SearXNG issue #6779](https://github.com/searxng/searxng/issues/6779).
Compare a query using `all` with one using a specific language.

Optional settings belong in the **`mcp-search` service environment**:

```yaml
SEARXNG_DEFAULT_LANGUAGE: en
SEARXNG_TIMEOUT_MS: "20000"
```

The language default applies when a tool call omits `language`. Coordinate MCP
and SearXNG timeouts, and recreate `mcp-search` after environment changes.
See the [MCP configuration](https://github.com/ihor-sokoliuk/mcp-searxng/blob/main/CONFIGURATION.md)
and [SearXNG outgoing settings](https://docs.searxng.org/admin/settings/settings_outgoing.html).

</details>

## Project structure

```text
app/
├── agents/       # Graph, model calls, and tool execution
├── bot/          # Telegram command registration and routing
├── clients/      # LLM and MCP clients
├── controllers/  # Request handling and error reporting
├── core/         # Settings, prompts, and logging
├── models/       # Request, response, and history types
├── services/     # Response generation and conversation branching
└── views/        # Rich Messages and Telegram delivery

docs/prompts.yml  # Command descriptions and mode prompts
searxng/          # Search service configuration
data/             # SQLite storage; excluded from Git
main.py           # Application entry point
```

## Privacy and limitations

- Keep `.env`, proxy credentials, and private search settings out of public commits.
  `.env` and `data/` are ignored by Git; search configuration must be reviewed separately.
- Conversation checkpoints contain messages and tool results. The LLM provider
  receives the conversation context; search services receive search queries.
- Enable `CHECK_HISTORY` with care in shared chats: the summary includes earlier
  messages and tool output.
- Search availability depends on external engines, network access, and the
  provider's tool-calling support. Model answers can still contain mistakes.
- Message splitting follows text boundaries and size, not Markdown structure;
  very long code blocks or tables may be split across messages.

---

<div align="center">

Search · read · remember · reply

[MIT License](LICENSE)

</div>
