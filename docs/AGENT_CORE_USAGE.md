# 🔥 Devil Agent — Complete Usage Guide

This repository ships **two cooperating components** that together form the Devil Agent platform:

| Component | Path | What it does |
|-----------|------|--------------|
| **Web app** | `backend/` + `frontend/` | The user-facing site at **https://your-domain.com** — signup with 40-word key, login, chat history, skills, settings. FastAPI + React + MongoDB. |
| **Agent core** | `agent_core/` | The autonomous AI brain — a full Hermes/Devil Agent runtime with tool use, skills, plugins, browser, terminal, memory, and an **OpenAI-compatible HTTP API** on port 9241 (publicly exposed at `https://your-domain.com/agent/v1/...`). |

They work together: the web frontend gives you chat / skills / accounts, and the agent core gives you a real tool-using AI you can talk to programmatically or through any OpenAI-compatible client.

---

## 🌐 Live URLs

| What | URL |
|------|-----|
| Web UI | https://your-domain.com |
| Web API | https://your-domain.com/api |
| **Agent API (OpenAI-compatible)** | **https://your-domain.com/agent/v1** |
| Agent health | https://your-domain.com/agent/health |
| Agent models | https://your-domain.com/agent/v1/models |

**Agent API key** (Bearer token): configured per deployment in `agent_core/.env` → `API_SERVER_KEY`.

---

## 1. Using the Agent core API

The agent exposes the **OpenAI Chat Completions** schema so anything that speaks OpenAI speaks Devil Agent.

### Curl example

```bash
curl -X POST https://your-domain.com/agent/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Write a python one-liner to print primes under 50"}]
  }'
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-domain.com/agent/v1",
    api_key="YOUR_API_SERVER_KEY",
)

resp = client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)
```

### Plug it into any OpenAI-compatible UI
Open WebUI, LobeChat, LibreChat, AnythingLLM, NextChat, ChatBox, etc. — set:
- **Base URL**: `https://your-domain.com/agent/v1`
- **API key**: `API_SERVER_KEY` from your `.env`

### Available endpoints
- `GET  /agent/health` — health probe
- `GET  /agent/v1/models` — list models
- `GET  /agent/v1/capabilities` — machine-readable capability map
- `POST /agent/v1/chat/completions` — OpenAI chat completions (sync + SSE streaming)
- `POST /agent/v1/responses` — OpenAI Responses API (stateful)
- `POST /agent/v1/runs` — async agent run (returns `run_id`)
- `GET  /agent/v1/runs/{run_id}` — poll run status
- `GET  /agent/v1/runs/{run_id}/events` — SSE event stream

---

## 2. Using the Agent core CLI on the VPS

After `ssh -i your-ssh-key.pem ubuntu@YOUR_VPS_IP`:

```bash
devil                                     # interactive chat
devil --query "summarise this dir" -t terminal,web
devil --skills github-pr-workflow -q "open a PR for current branch"
devil --help                              # full flag list
```

The `devil` wrapper is installed at `/usr/local/bin/devil` and points to `/path/to/devil_agent/agent_core/devil`, which activates the venv, exports `.env`, and runs `cli.py --provider nvidia --model meta/llama-3.3-70b-instruct`.

Useful CLI flags:
- `--query, -q` — one-shot prompt (no REPL)
- `--toolsets, -t web,terminal,vision,...` — enable toolsets
- `--skills, -s name1,name2` — preload skills
- `--model` / `--provider` — override defaults
- `--resume SESSION_ID` — continue a previous session

---

## 3. Web app + Agent core together

The web app at `backend/server.py` is a self-contained FastAPI (40-word key auth, conversation history, NVIDIA chat). It currently calls NVIDIA directly — but you can **point it at the agent core instead** to get tool-use, skills and memory inside the web chat.

In `backend/.env`, swap the NVIDIA endpoint to the local agent core:
```
NVIDIA_API_BASE=http://127.0.0.1:9241/v1
NVIDIA_API_KEY=YOUR_API_SERVER_KEY      # the agent's API_SERVER_KEY
DEFAULT_MODEL=meta/llama-3.3-70b-instruct
```
Restart the backend service (`sudo systemctl restart devil-backend`) and every chat in the web UI will now flow through the agent (tool calls, skills, terminal, browser).

---

## 4. Services managed by systemd

| Service | What | Logs |
|---------|------|------|
| `devil-backend.service` | Web API (FastAPI, port 8001) | `journalctl -u devil-backend -f` |
| `devil-gateway.service` | **Agent core gateway (port 9241)** | `tail -f ~/.devil/logs/gateway.log` |
| `mongod.service` | MongoDB | `journalctl -u mongod -f` |
| `nginx.service` | TLS termination + reverse proxy | `tail -f /var/log/nginx/error.log` |

Restart agent core: `sudo systemctl restart devil-gateway`

---

## 5. Configuration

| File | Purpose |
|------|---------|
| `backend/.env` | Web API secrets, MongoDB URL, JWT secret, NVIDIA key |
| `agent_core/.env` | Agent NVIDIA key, API_SERVER_KEY, port |
| `agent_core/cli-config.yaml` | Agent provider/model, performance, enabled platforms |
| `~/.devil/config.yaml` | Active gateway config (a copy of `cli-config.yaml`) |
| `/etc/nginx/sites-enabled/devil_agent` | Routes `/` → frontend build, `/api/` → 8001, `/agent/` → 9241, `/ws/` → 8001 |

---

## 6. Quick installation on a fresh VPS

```bash
# 1. Clone
cd /home/ubuntu
git clone https://github.com/YOUR_GITHUB_USERNAME/devil-agent-ai-platform.git devil_agent
cd devil_agent

# 2. Web (backend + frontend)
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in MONGO_URL, JWT_SECRET, ENCRYPTION_KEY, NVIDIA_API_KEY
cd ../frontend && yarn install && yarn build

# 3. Agent core
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
cd /path/to/devil_agent/agent_core
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env  # fill in NVIDIA_API_KEY, API_SERVER_KEY
cp cli-config.yaml ~/.devil/config.yaml  # mkdir -p first
sudo ln -sf $PWD/devil /usr/local/bin/devil

# 4. systemd units (devil-backend.service, devil-gateway.service)
# 5. nginx site (TLS via certbot)
sudo systemctl daemon-reload
sudo systemctl enable --now mongod devil-backend devil-gateway nginx
```

---

## 7. Sanity-check checklist

```bash
curl https://your-domain.com/                         # frontend
curl https://your-domain.com/api/                     # web api
curl https://your-domain.com/agent/health             # agent health
curl https://your-domain.com/agent/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"
```

All four should return JSON / HTML 200s.
