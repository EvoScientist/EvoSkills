# MCP Servers

This directory contains the **MCP (Model Context Protocol) server marketplace** for EvoSkills. Each `.yaml` file defines one MCP server that agents can discover and connect to.

## How It Works

EvoScientist discovers these servers by shallow-cloning this repository and scanning `mcp/*.yaml`. The parsed entries power:

- **`/install-mcp`** — interactive browser (tag picker → server selector) in both CLI and TUI modes
- **`EvoSci mcp install <name>`** — direct install by server name or tag
- **`EvoSci onboard`** — the onboarding wizard offers servers tagged `onboarding`

When a user installs a server:

1. If `pip_package` is set, the package is auto-installed (`uv pip install` if available, else `pip install`)
2. If `env_key` is set, the user is prompted with `env_hint` to configure the required API key
3. The server entry is written to the user's local config at `~/.config/evoscientist/mcp.yaml`

Once installed, the server is available to all agents in future EvoScientist sessions.

## Available Servers

| Server | Description | Transport |
| ------ | ----------- | --------- |
| [`arxiv`](arxiv.yaml) | Search & fetch academic papers from arXiv | stdio |
| [`context7`](context7.yaml) | Fast documentation lookup for libraries and frameworks | stdio |
| [`deepwiki`](deepwiki.yaml) | Search & read GitHub repo documentation | streamable_http |
| [`docs-langchain`](docs-langchain.yaml) | Documentation for building agents with LangChain | streamable_http |
| [`exa`](exa.yaml) | Neural web search and content retrieval | http |
| [`perplexity`](perplexity.yaml) | AI-powered web search via Perplexity | stdio |
| [`sequential-thinking`](sequential-thinking.yaml) | Chain-of-thought reasoning with sequential thinking steps | stdio |
| [`ssh`](ssh.yaml) | Remote command execution and file transfer over SSH | stdio |

## Contributing an MCP Server

### Server Anatomy

Each server is a single YAML file under `mcp/`:

```
mcp/
  my-server.yaml    # one file per server — filename must match the name field
```

### YAML Schema

Every server definition must include these required fields:

```yaml
name: my-server                           # unique identifier (lowercase, hyphens)
label: "My Server  (short human-readable summary)"
description: "What this server does"
tags: [category]                          # at least one tag
transport: stdio                          # one of: stdio, http, streamable_http
```

Plus transport-specific fields (see below).

### Transport Types

#### `stdio` — local process

The agent spawns a local process and communicates over stdin/stdout.

```yaml
transport: stdio
command: npx                              # executable to run
args: ["-y", "@my-org/my-mcp-server"]     # command arguments
```

If the server is a Python package installable via pip:

```yaml
transport: stdio
command: my-mcp-server
args: []
pip_package: my-mcp-server                # auto-installed via uv/pip before first use
```

#### `http` / `streamable_http` — remote endpoint

The agent connects to a hosted URL. No local process needed.

```yaml
transport: http                           # or streamable_http
url: "https://mcp.example.com/mcp"
```

You can optionally include HTTP headers:

```yaml
headers:
  Authorization: "Bearer ${MY_TOKEN}"
```

### Environment Variables

If the server requires or benefits from an API key or other env var:

```yaml
env:
  MY_API_KEY: "${MY_API_KEY}"             # interpolated from the user's environment at runtime
env_key: MY_API_KEY                       # the env var the installer checks for
env_hint: "export MY_API_KEY=... (get one at example.com/settings)"
```

If the env var is **optional** (server works without it but unlocks extras like higher rate limits), add:

```yaml
env_optional: true
```

Omit `env_optional` (or set it to `false`) when the server **cannot function** without the key.

### Tags

Tag your server with at least one category so agents and users can filter the marketplace. Existing tags:

- `academic-search` — paper / citation search
- `web-search` — general web search
- `documentation` — docs and reference lookup
- `reasoning` — thinking and reasoning tools
- `remote-execution` — remote / SSH execution

Create a new tag only if none of the existing ones fit.

### Field Reference

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `name` | string | yes | Unique identifier (lowercase, hyphens). Must match filename. |
| `label` | string | yes | Human-readable name shown in the browser UI. |
| `description` | string | yes | What the server does. |
| `tags` | list | yes | At least one tag for filtering. |
| `transport` | string | yes | `stdio`, `http`, or `streamable_http`. |
| `command` | string | stdio only | Executable to run. |
| `args` | list | stdio only | Command-line arguments. |
| `url` | string | http only | Server endpoint URL. |
| `headers` | dict | no | HTTP headers (http/streamable_http). |
| `pip_package` | string | no | Python package auto-installed before first use. |
| `env` | dict | no | Environment variables passed to the process. Values use `${VAR}` for runtime interpolation. |
| `env_key` | string | no | The env var name the installer checks and prompts for. |
| `env_hint` | string | no | User-facing hint shown when prompting for `env_key`. |
| `env_optional` | bool | no | `true` if the server works without `env_key`. Default: `false`. |

## Full Example

A complete example combining all optional fields:

```yaml
name: my-server
label: "My Server  (neural code search with optional API key)"
description: "Search codebases using neural embeddings"
tags: [code-search]
transport: stdio
command: npx
args: ["-y", "@my-org/my-mcp-server"]
env:
  MY_API_KEY: "${MY_API_KEY}"
env_key: MY_API_KEY
env_hint: "export MY_API_KEY=... (get one at example.com/api)"
env_optional: true
```

## Checklist

Before submitting a PR:

- [ ] Filename matches the `name` field (`my-server.yaml` has `name: my-server`)
- [ ] `label` and `description` are filled in
- [ ] At least one `tag` is set
- [ ] Transport-specific fields are correct (`command`/`args` for stdio, `url` for http)
- [ ] If an API key is needed, `env`, `env_key`, and `env_hint` are set
- [ ] The YAML is valid (no syntax errors)
- [ ] You've tested that the server connects and responds
