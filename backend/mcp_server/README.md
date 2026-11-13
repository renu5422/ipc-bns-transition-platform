# IPC-BNS MCP Server

Exposes the IPC → BNS transition platform as a **Model Context Protocol (MCP)** server, so any MCP-capable client (Claude Desktop, Claude Code, custom agents) can call the platform's search, mapping, contradiction-detection, summarization, and agentic Q&A capabilities as tools.

Server name: `ipc-bns-legal-intelligence`
Transport: stdio (default)
LLM: offline `DeterministicLegalLLM` fallback — **no API keys required**.

## Requirements

```bash
pip install mcp
```

(Add `mcp>=1.0.0` to `backend/requirements.txt`.)

## Running the server

From the repository root (so that `backend/` and `data/` resolve):

```bash
python -m backend.mcp_server.server
```

The server speaks MCP over stdin/stdout and waits for a client to connect. It is not meant to be run interactively — register it with a client as shown below.

## Registering in Claude Desktop

Add to your Claude Desktop config file (`claude_desktop_config.json`):

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ipc-bns-legal-intelligence": {
      "command": "python",
      "args": ["-m", "backend.mcp_server.server"],
      "cwd": "/absolute/path/to/ipc-bns-transition-platform"
    }
  }
}
```

Restart Claude Desktop; the five tools appear under the server name. If Claude Desktop ignores `cwd` on your platform, use a small wrapper script that `cd`s into the repo first, or set `"args": ["-m", "backend.mcp_server.server"]` with `"command"` pointing at a venv Python whose working directory is the repo.

## Registering in Claude Code

```bash
cd /path/to/ipc-bns-transition-platform
claude mcp add ipc-bns-legal-intelligence -- python -m backend.mcp_server.server
```

Verify with `claude mcp list`.

## Tools

| Tool | Signature | Purpose |
|---|---|---|
| `search_sections` | `(query: str, limit: int = 5)` | Keyword/full-text search over IPC↔BNS mappings |
| `get_mapping` | `(code: str)` | Exact mapping lookup for a section code |
| `detect_contradictions` | `()` | Scan the whole dataset for conflicting mappings |
| `summarize_section` | `(code: str)` | Plain-language summary of one section |
| `ask_legal_agent` | `(question: str)` | Full multi-step agent run with audit trace |

### Example calls

**search_sections**

```json
{"tool": "search_sections", "arguments": {"query": "murder", "limit": 5}}
```

Returns `{"query", "count", "results": [{"id", "score", "record"}, ...]}` where each `record` has `ipc_code`, `bns_code`, titles, description, chapter, keywords.

**get_mapping**

```json
{"tool": "get_mapping", "arguments": {"code": "IPC-302"}}
```

Returns `{"code": "IPC-302", "count": 1, "mappings": [...]}`; codes are normalized (`ipc 302` → `IPC-302`). Unknown codes return `{"error": "...", "code": "..."}`.

**detect_contradictions**

```json
{"tool": "detect_contradictions", "arguments": {}}
```

Returns `{"count": N, "contradictions": [{"type", "code", "ids"}, ...]}`.

**summarize_section**

```json
{"tool": "summarize_section", "arguments": {"code": "IPC-302"}}
```

Returns `{"code", "ipc_code", "bns_code", "summary", "model"}`; unknown codes return an `{"error": ...}` dict instead of raising.

**ask_legal_agent**

```json
{"tool": "ask_legal_agent", "arguments": {"question": "What replaced IPC-302 under the BNS?"}}
```

Returns `{"answer", "references", "sources", "contradictions", "confidence", "trace", "model"}` — `trace` records every pipeline step for auditability.

## Testing

```bash
pytest tests/test_mcp_server.py -q
```

Tests call the tool implementation functions directly (no stdio transport, no network) and are skipped automatically if the `mcp` package is not installed.
