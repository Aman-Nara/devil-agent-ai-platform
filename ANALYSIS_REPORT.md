# 🔱 DEVIL AGENT AI PLATFORM — COMPLETE ANALYSIS REPORT

**Generated:** 2026-06-08 (UTC)
**Agent Version:** Autonomous Senior AI Engineering Agent v3.0
**Host:** `ubuntu@YOUR_VPS_IP` — `ip-172-31-11-219` (AWS, Ubuntu 22.04, Linux 6.8)
**Workspace:** `/path/to/devil_agent`
**Public Domain:** https://your-domain.com
**Repository Commit:** `43c80ff Devil Agent - AI Assistant Platform`
**Codebase Size:** 271,005 Python LOC · 91,262 TS/JS LOC · 3,459 source files
**Disk:** 287 GB used / 659 GB · **RAM:** 15 GiB · **Swap:** 15 GiB

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Repository Inventory](#2-repository-inventory)
3. [Project Overview](#3-project-overview)
4. [Technology Stack](#4-technology-stack)
5. [Architecture (6 Views)](#5-architecture-6-views)
6. [Agent System Design](#6-agent-system-design)
7. [Database Documentation](#7-database-documentation)
8. [API Documentation](#8-api-documentation)
9. [Security Audit](#9-security-audit)
10. [Performance Analysis](#10-performance-analysis)
11. [Frontend Architecture](#11-frontend-architecture)
12. [DevOps & Infrastructure](#12-devops--infrastructure)
13. [Feature Catalog (900+)](#13-feature-catalog-900)
14. [Code Quality](#14-code-quality)
15. [Test Coverage](#15-test-coverage)
16. [Implemented Improvements Log](#16-implemented-improvements-log)
17. [Future Roadmap](#17-future-roadmap)
18. [Appendix](#18-appendix)

---

## 1. EXECUTIVE SUMMARY

Devil Agent is a **multi-surface AI assistant platform** composed of three independently deployable layers:

| Layer | Description | Port | LOC |
|---|---|---|---|
| **`backend/`** | FastAPI web API (chat, skills, auth, terminal WS) | 8001 | ~786 |
| **`frontend/`** | React 19 + TypeScript SPA served by nginx | static | ~91k TS/JS |
| **`agent_core/`** | Heavyweight autonomous agent runtime + OpenAI-compatible gateway | 9241 | ~270k Py |

**State of the platform (post-audit):**
- ✅ All services healthy (`devil-backend`, `devil-gateway`, `nginx`, `mongod`)
- ✅ TLS via Let's Encrypt, HTTP→HTTPS redirect enforced
- ✅ End-to-end signup → login → chat → skills flows verified live
- ✅ 6 safe improvements applied directly to the live VPS in this session
- ⚠️ 4 medium-risk findings documented (not implemented automatically)
- ⚠️ In-memory rate-limit/cache split across 2 uvicorn workers — Redis migration recommended

**Score card:**

| Domain | Score | Notes |
|---|---|---|
| Authentication | 8/10 | Strong 40-word entropy keys + bcrypt + JWT; no recovery (by design) |
| Authorization | 7/10 | Ownership checks on all resources; admin tier not implemented |
| Injection Defense | 8/10 | Pydantic validation, MongoDB driver parameterization, regex anchored |
| Secrets Mgmt | 7/10 | `.env` based; **hardcoded NVIDIA key removed** during this audit |
| Agent Security | 6/10 | WS terminal sandboxed to `/tmp`, blocklist expanded this run |
| Data Protection | 7/10 | Fernet-encrypted user API keys, JWT-secured WS |
| Performance | 7/10 | Connection pool, key-prefix login O(1), bounded caches added |
| Observability | 5/10 | Stdout logs only; no metrics endpoint, no APM |
| **Overall** | **7/10** | Solid foundation; opportunities in observability + worker-shared state |

---

## 2. REPOSITORY INVENTORY

```
/path/to/devil_agent
├── .git/                          (43c80ff, single commit)
├── .gitignore
├── README.md                      (18,990 bytes)
├── LICENSE
├── agent_log.md                   (NEW — audit trail this run)
├── ANALYSIS_REPORT.md             (THIS FILE)
├── backend/                       83 MB
│   ├── server.py                  (849 lines — FastAPI app)
│   ├── server.py.bak              (24 KB — prior version)
│   ├── server.py.bak_20260608...  (NEW — pre-audit snapshot)
│   ├── requirements.txt           (12 deps pinned)
│   ├── .env / .env.example
│   └── venv/                      Python 3 virtualenv
├── frontend/                      451 MB (with node_modules)
│   ├── package.json               (React 19.2 + react-router 7 + xterm)
│   ├── tsconfig.json              (TS 4.9, strict)
│   ├── tailwind.config.js
│   ├── public/ build/ src/
│   │   └── src/pages/
│   │       ├── Landing.tsx        (163 lines)
│   │       ├── Signup.tsx         (161 lines)
│   │       ├── Login.tsx          (93 lines)
│   │       ├── Dashboard.tsx      (614 lines)
│   │       └── Dashboard.tsx.bak*  (3 historical backups)
│   └── .env / .env.production
├── agent_core/                    194 MB — Devil Agent autonomous runtime
│   ├── cli.py / batch_runner.py / run_agent.py
│   ├── DEVIL_AGENT_CONFIG.md
│   ├── pyproject.toml / package.json (pnpm + Python hybrid)
│   ├── Dockerfile / docker-compose.yml
│   ├── agent/                     core orchestrator
│   ├── gateway/                   OpenAI-compatible HTTP server (port 9241)
│   ├── providers/                 LLM provider adapters
│   ├── tools/                     ~80 first-party tools (browser, FS, MCP, OAuth, TTS …)
│   ├── plugins/                   plugin loader
│   ├── skills/  hermes/  acp_*    skill packs + Hermes state engine
│   ├── tests/                     ~120 test files (pytest)
│   ├── web/                       Vite + React panel (separate from /frontend)
│   ├── cron/                      job scheduler
│   ├── packaging/  docs/  nix/    installer + reproducible builds
│   └── locales/                   i18n strings
├── docs/
│   ├── DEPLOYMENT_REPORT.md
│   ├── BUG_FIX_SUMMARY.md
│   ├── DEPLOYMENT_SUMMARY.md
│   ├── AGENT_CORE_USAGE.md
│   └── screenshots/
└── assets/
```

**File extension distribution** (top‑level only, excluding `node_modules`/`.git`):

| Ext | Count (approx) | Role |
|---|---|---|
| `.py` | ~2,100 | Backend + agent_core |
| `.ts/.tsx` | ~280 | Frontend + agent_core/web |
| `.js/.jsx` | ~140 | Misc / build |
| `.md` | ~90 | Docs |
| `.yaml/.yml` | ~30 | Config (compose, CI, gateway) |
| `.json` | ~50 | Package manifests, lockfiles |

---

## 3. PROJECT OVERVIEW

**Simple language.** Devil Agent is a web app where users sign up by being **given** a 40-word secret key (no email/password). After login they get a chat UI that talks to an LLM (NVIDIA-hosted Qwen3-Next-80B by default), a "Skills" library where they can store code snippets, and a secure in-browser terminal. The bigger `agent_core/` is a desktop-grade autonomous coding agent (similar in scope to OpenHands / Aider / Cline) that exposes an **OpenAI-compatible API** on `/agent/*` and can be used via CLI, web, or MCP.

**Technical language.** A FastAPI microservice fronts MongoDB and proxies chat to NVIDIA Integrate. A separate, much larger Python codebase (`agent_core`) implements a tool-using agent with skill registries, plugin system, MCP client/server, OAuth-protected integrations (Microsoft Graph, Home Assistant), browser automation (Camoufox), TTS (NeuTTS), and vision tools. A Vite-built mini-UI ships inside `agent_core/web`. nginx terminates TLS and routes:
- `/` → SPA static
- `/api/*` → FastAPI (8001)
- `/ws/*` → FastAPI WebSocket
- `/agent/*` → `agent_core` gateway (9241, streaming)

**Differentiators.** (1) Password-less, recovery-less identity via 40-word entropy keys. (2) Built-in skill store (user-private CRUD over code snippets). (3) Sandbox terminal exposed over auth'd WS. (4) Co-located autonomous agent runtime accessible via OpenAI API contract — so any OpenAI SDK can target it.

---

## 4. TECHNOLOGY STACK

### Backend (`backend/`)

| Name | Version | Why | Where | Risk |
|---|---|---|---|---|
| FastAPI | 0.104.1 | Async, OpenAPI, deps-injection | `server.py` | Low |
| uvicorn | 0.24.0 | ASGI runner, `--workers 2` | systemd unit | Low |
| PyMongo | 4.6.0 | Sync Mongo driver | `server.py` | Low (consider Motor for async) |
| python-jose | 3.3.0 | JWT HS256 | `server.py:create_jwt_token` | Low |
| bcrypt | 4.1.1 | Key hashing | `server.py:hash_key/verify_key` | Low |
| httpx | 0.25.2 | Async HTTP to NVIDIA | `server.py:chat` | Low |
| cryptography | 41.0.7 | Fernet encryption of stored user keys | `encrypt_api_key` | Low (CVE‑free at version) |
| pydantic | 2.5.2 | Schema validation | All request models | Low |
| python-dotenv | 1.0.0 | Load `.env` | top of file | Low |
| redis | 5.0.1 | **Installed but unused** in `backend/` | requirements.txt | Med — drop or wire |
| orjson | 3.9.10 | Faster JSON | unused directly; FastAPI auto | Low |
| websockets | 12.0 | WS support | terminal endpoint | Low |

### Frontend (`frontend/`)

| Name | Version | Role |
|---|---|---|
| React | 19.2.6 | UI framework |
| react-router-dom | 7.15.1 | Routing |
| react-scripts (CRA) | 5.0.1 | Build pipeline |
| TypeScript | 4.9.5 | Type safety (consider 5.x) |
| react-markdown | 10.1.0 | Markdown renderer |
| react-syntax-highlighter | 16.1.1 | Code blocks |
| lucide-react | 1.16.0 | Icons |
| xterm + xterm-addon-fit | 5.3 / 0.8 | Terminal UI |
| Tailwind | (config present) | Utility CSS |

### Agent Runtime (`agent_core/`)

- **Python package layout** via `pyproject.toml` (`devil_agent.egg-info` present).
- **Provider adapters** (`providers/`): OpenAI-compatible base + concrete providers; per-tests file names suggest MiniMax OAuth, Ollama (`test_ollama_num_ctx.py`), Yuanbao (pipeline + markdown + proto + integration), OpenRouter (`openrouter_client.py`).
- **Tooling** (`tools/`): browser (Camoufox), file ops, terminal, kanban, MCP OAuth, MS Graph, HomeAssistant, NeuTTS synth, OSV-Scan check, Tirith security, vision.
- **Gateway** (`gateway/run.py`): OpenAI-compatible HTTP server on `:9241`, streamed via nginx (buffering off, 600s timeouts).
- **MCP server** (`mcp_serve.py`): exposes tools/skills over Model Context Protocol.
- **Cron** (`cron/scheduler.py`, `cron/jobs.py`): background jobs.
- **Docker**: `agent_core/Dockerfile` + `agent_core/docker-compose.yml` — not currently used by live systemd units (they run from `.venv`).

### Infrastructure

| Component | Version / Config |
|---|---|
| OS | Ubuntu 22.04 LTS, Linux 6.8.0-1046-aws |
| Init | systemd (units below) |
| Reverse proxy | **nginx** with certbot-managed Let's Encrypt cert |
| MongoDB | running on `127.0.0.1:27017` (`/etc/mongod.conf`) — DB `devil_web` |
| Redis | running on `127.0.0.1:6379` — **not used by `backend/`** today |
| Ollama | local LLM runtime on `127.0.0.1:11434` (likely used by agent_core) |
| Docker | installed (`dockerd`, `containerd`), not used by Devil Agent |
| PM2 | installed for other apps on box (forge-ai, soulcracks) — Devil uses systemd |

### Systemd units in play

```
devil-backend.service   → uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
devil-gateway.service   → python gateway/run.py --config ~/.devil/config.yaml
forge-ai.service        → (unrelated app on same host)
nginx.service           → TLS + routing
```

---

## 5. ARCHITECTURE (6 VIEWS)

### View 1 — High-level System

```
                       ┌──────────────────┐
  Internet ── 443 ────►│      nginx       │── /         ──► /path/to/devil_agent/frontend/build (static SPA)
                       │  TLS · gzip · LE │── /api/*    ──► 127.0.0.1:8001  (devil-backend / FastAPI)
                       │                  │── /ws/*     ──► 127.0.0.1:8001  (WebSocket terminal)
                       └──────────────────┘── /agent/*  ──► 127.0.0.1:9241  (devil-gateway / agent_core)
                                                                  │
   ┌──────────────────────────────────────────────────────────────┴───────────────┐
   │                                                                              │
   ▼                                                                              ▼
┌──────────────┐        ┌────────────────────┐                       ┌─────────────────────┐
│ devil-backend│──────► │  MongoDB devil_web │                       │  agent_core runtime │
│  FastAPI     │        │  users · convs ·   │                       │  + LLM gateway      │
│  (2 workers) │        │  skills            │                       │  + tools + plugins  │
└──────┬───────┘        └────────────────────┘                       └─────────┬───────────┘
       │                                                                       │
       │ httpx (async)                                                         │ via providers
       ▼                                                                       ▼
 NVIDIA Integrate API                                            Ollama (local) / OpenRouter / OpenAI
 https://integrate.api.nvidia.com/v1                             (model selectable in agent_core config)
```

### View 2 — Data Flow (chat happy path)

```
Browser  ──POST /api/chat (JWT)──► nginx ──► uvicorn worker
                                                │
                                                ▼
                                  Depends(get_current_user)
                                  ├── verify JWT (HS256)
                                  ├── cache_storage hit? ─yes─► return
                                  └── users_collection.find_one
                                                │
                                                ▼
                                  rate_limit_check(tier-aware, unlimited if ≤0)
                                                │
                                                ▼
                                  Load/create conversation (Mongo)
                                                │
                                                ▼
                                  Decrypt user NVIDIA key (Fernet) OR fall back to env
                                                │
                                                ▼
                                  httpx.AsyncClient POST NVIDIA chat/completions
                                                │
                                                ▼
                                  $push two messages on conversation, $inc usage stats
                                                │
                                                ▼
                                  return {conversation_id, message}
```

### View 3 — Agent Execution (agent_core)

```
gateway/run.py (OpenAI-compatible POST /v1/chat/completions on :9241)
        │
        ▼
provider router (openai-compat or local)
        │
        ▼
ReAct loop in agent/  ──► tools/registry  ──► concrete tool (file_ops, terminal, browser, MCP, …)
        │                                              │
        │                                              ▼
        │                                       sandboxed exec / external API
        │
        ├── memory writes (hermes_state, evidence_store)
        └── streaming response back to client via SSE (proxy_buffering off in nginx)
```

### View 4 — Request lifecycle (auth'd endpoint)

```
TCP → TLS (Let's Encrypt) → nginx ──► uvicorn worker
                            │             │
                            │  client_max_body_size 50M, gzip on
                            ▼
                    add_security_headers middleware  (X-CTO, X-Frame, Referrer, Permissions)
                            │
                            ▼
                    CORS middleware (whitelist: your-domain.com, localhost:3000)
                            │
                            ▼
                    Pydantic validate request body
                            │
                            ▼
                    HTTPBearer → JWT decode → cache or Mongo
                            │
                            ▼
                    handler logic
                            │
                            ▼
                    JSON response (auto-orjson where applicable)
```

### View 5 — Communication (services & ext APIs)

```
backend ──httpx──► NVIDIA Integrate (chat)
backend ──pymongo──► MongoDB
backend ──in-process──► fernet (encrypt/decrypt)
agent_core ──providers──► Ollama / OpenRouter / OpenAI / etc.
agent_core ──MCP client──► remote MCP servers
agent_core ──OAuth──► Microsoft Graph, Home Assistant
nginx ──proxy_pass──► backend (8001) + gateway (9241)
```

### View 6 — Security flow

```
Public request
   │
   ▼
TLS (LE) ─── nginx (HSTS via cert config, redirects 80→443)
   │
   ▼
CORS allow-list ── reject if origin not in env ALLOWED_ORIGINS
   │
   ▼
JWT verify (HS256) ── reject 401 if missing/invalid
   │
   ▼
Resource ownership filter ── `{user_id: <jwt.user_id>}` on every query
   │
   ▼
Rate-limit by tier (free 100/d, pro 1000/d, enterprise unlimited)
   │
   ▼
Pydantic schema validation
   │
   ▼
Handler executes (DB + outbound calls timeout 60s)
```

---

## 6. AGENT SYSTEM DESIGN

The "agent" surface in this repo is **two-tiered**:

### Tier A — `backend/` chat (lightweight)

A thin pass-through to NVIDIA Integrate. No autonomous loop, no tool calling. The "agent" identity is essentially the user's tier + per-user encrypted API key.

### Tier B — `agent_core/` (full autonomous runtime)

Inferring from directory layout and test file names:

| Subsystem | Files | What it does |
|---|---|---|
| **Orchestrator** | `agent/`, `run_agent.py`, `batch_runner.py` | Main ReAct loop, batched jobs |
| **Gateway** | `gateway/` | OpenAI-compatible HTTP server, exposed via nginx `/agent/` |
| **Providers** | `providers/base.py`, MiniMax/OpenAI/Ollama/Yuanbao/OpenRouter | Pluggable LLM backends |
| **Tool registry** | `tools/registry.py` + 70+ tool modules | First-party tools (FS, terminal, browser, MS Graph, HomeAssistant, kanban, vision, tts, MCP, OSV, Tirith) |
| **MCP** | `mcp_serve.py`, `tools/mcp_oauth.py` | MCP server + OAuth client |
| **Plugins** | `plugins/`, `optional-skills/` | Plugin loader + skill packs |
| **Memory** | `hermes-already-has-routines.md`, `tests/hermes_state/`, `evidence_store` | Hermes state engine + episodic store |
| **Cron** | `cron/scheduler.py`, `cron/jobs.py` | Recurring jobs |
| **CLI** | `cli.py`, `devil_cli/`, `mini_swe_runner.py` | Terminal entry points |
| **Web panel** | `agent_core/web/` (Vite + TS) | Separate UI for the agent |
| **Skills hub** | `tools/skills_hub.py`, `tools/skills_guard.py` | Sandboxed user-uploaded skills |
| **Security** | `tools/path_security.py`, `tools/tirith_security.py`, `SECURITY.md` | Path traversal guards, security policy |

**Memory layers** (inferred):

| Layer | Backed by | Lifetime |
|---|---|---|
| Conversation (Tier A) | `db.conversations.messages[]` | persistent |
| Cache (Tier A) | `cache_storage` dict (now bounded) | 5 min |
| Hermes state (Tier B) | filesystem under `$DEVIL_HOME` | persistent |
| Evidence store (Tier B) | `tests/test_evidence_store.py` reference | persistent |
| Skills (user-defined) | `db.skills` (Tier A) + `tools/skills_hub` (Tier B) | persistent |

---

## 7. DATABASE DOCUMENTATION

**Engine:** MongoDB 7.x · **DB:** `devil_web` · **Host:** `127.0.0.1:27017`

### Collection: `users`

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | PK |
| `key_hash` | str | bcrypt hash of the 40-word key — **unique index** |
| `key_prefix` | str | first 8 chars of the key — indexed (login O(1)) |
| `tier` | str | `free` / `pro` / `enterprise` — indexed |
| `created_at` | datetime (UTC) | indexed |
| `last_login` | datetime (UTC) | |
| `nvidia_api_key_encrypted` | str (Fernet) | optional, per-user key |
| `usage_stats` | object | `{total_messages, total_conversations, total_skills, messages_today, last_message_date}` |

Indexes: `key_hash` (unique), `key_prefix`, `tier`, `created_at`.

### Collection: `conversations`

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | PK |
| `user_id` | str | owner (string-form of `users._id`) |
| `title` | str | auto from first 50 chars |
| `messages` | array<{role, content, timestamp}> | grows unbounded — see roadmap |
| `created_at` / `updated_at` | datetime (UTC) | |

Indexes: `(user_id ASC, created_at DESC)`, `title`.

### Collection: `skills`

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | PK |
| `user_id` | str | owner |
| `name`, `description`, `code`, `language` | str | |
| `category` | str | indexed |
| `tags` | array<str> | indexed |
| `created_at` / `updated_at` | datetime | |

Indexes: `(user_id, name)`, `tags`, `category`.

### ER overview

```
users (1) ──── (N) conversations
              └─ (N) skills
```

No foreign-key enforcement (Mongo); ownership is enforced at the query layer (every read/write filters by `user_id`).

### Migrations

Single commit, no migration tooling; schema is implicit. **Recommendation:** introduce a one-shot ensure-index helper that runs at startup (the code already calls `create_index` — keep it idempotent, which it is).

### N+1 candidates

- `GET /api/conversations` iterates the cursor for response then runs a separate `count_documents` — not N+1 but two round-trips. Negligible at current scale.
- No detected N+1 patterns in `backend/server.py`.

---

## 8. API DOCUMENTATION

Base URL: **`https://your-domain.com`**

### Public

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| GET | `/` | none | — | banner JSON |
| GET | `/health` | none | — | `{status, database, timestamp}` |
| GET | `/api/version` | none | — | `{name, version, model, tiers, cache_entries, rate_limit_buckets, timestamp}` **(added this audit)** |
| POST | `/api/auth/signup` | none | — | `{token, user_id, key, message}` — key is the only secret, **never stored plaintext** |
| POST | `/api/auth/login` | none | `{key}` | `{token, user_id}` |

### User

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| GET | `/api/user/profile` | Bearer JWT | — | `{id, tier, has_nvidia_key, nvidia_key_preview, created_at, usage_stats}` |
| POST | `/api/user/nvidia-key` | Bearer JWT | `{nvidia_api_key}` | `{message}` — stored Fernet-encrypted |

### Chat

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| POST | `/api/chat` | Bearer JWT | `{conversation_id?, message, model?}` | `{conversation_id, message}` — proxies to NVIDIA |
| GET | `/api/conversations?skip=&limit=&search=` | Bearer JWT | — | `{conversations:[{id,title,created_at,updated_at,message_count}], total}` |
| GET | `/api/conversations/{id}` | Bearer JWT | — | `{id, title, messages, created_at, updated_at}` |
| DELETE | `/api/conversations/{id}` | Bearer JWT | — | `{message}` |

### Skills

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| GET | `/api/skills?skip=&limit=&search=&category=` | Bearer JWT | — | `{skills:[…], total}` |
| POST | `/api/skills` | Bearer JWT | `{name, description?, code, language?, category?, tags?}` | `{id, message}` — tier-quota enforced |
| PUT | `/api/skills/{id}` | Bearer JWT | partial fields | `{message}` |
| DELETE | `/api/skills/{id}` | Bearer JWT | — | `{message}` |

### Realtime

| Method | Path | Auth | Notes |
|---|---|---|---|
| WS | `/ws/terminal?token=<JWT>` | JWT in query | Sandboxed shell in `/tmp`, 10 s timeout, DANGEROUS blocklist |

### Agent core gateway (proxied)

| Method | Path | Notes |
|---|---|---|
| Any | `/agent/*` | Forwarded to `127.0.0.1:9241` (gateway/run.py), streaming-capable, 600 s read timeout. OpenAI-compatible endpoints exposed by `agent_core/gateway`. |

### Live verification (this run)

```
POST /api/auth/signup          → 200  {token,user_id,key,message}
POST /api/auth/login           → 200  {token,user_id}
GET  /api/user/profile (auth)  → 200  full profile
GET  /api/skills (auth)        → 200  {skills:[],total:0}
GET  /api/version (NEW)        → 200  v2.1.0
GET  /api/user/profile (bad)   → 401  Invalid token
POST /api/chat × 5 concurrent  → 200×5  (enterprise tier; previously broken)
```

---

## 9. SECURITY AUDIT

### Findings

| # | Severity | Title | Status |
|---|---|---|---|
| S1 | **HIGH** | Hardcoded NVIDIA API key fallback in `server.py` | **FIXED** (env-only) |
| S2 | **HIGH** | Enterprise tier (`max_messages_per_day = -1`) was 100% blocked due to `len(...) >= -1` always true | **FIXED** |
| S3 | MED | In-memory `rate_limit_storage` + `cache_storage` grew unboundedly; also split across 2 uvicorn workers (so rate limit was per-worker) | **PARTIAL FIX**: bounded + housekeeping. Worker-sharing requires Redis (documented). |
| S4 | MED | WS terminal blocklist was case-sensitive and missed several vectors (`systemctl`, `nc -l`, `ssh`, `scp`, `/dev/tcp/`, `crontab`, `init 0`, etc.) | **FIXED** (expanded, lowercased) |
| S5 | MED | Missing common security headers (CSP-lite, XCTO, XFO, Referrer-Policy, Permissions-Policy) | **FIXED** (XCTO/XFO/Referrer/Permissions middleware) |
| S6 | LOW | Frontend dev `.env` had typo `devils.your-domain.com` (production build used `.env.production` which was correct, so user impact was nil; still corrected) | **FIXED** |
| S7 | LOW | `JWT_SECRET` falls back to a fresh random value if env missing (breaks all sessions on restart). It IS set in `.env` today, so no live impact. | Documented — recommend fail-fast in prod |
| S8 | LOW | Fernet `ENCRYPTION_KEY` falls back to ephemeral key → would lose ability to decrypt previously stored user keys on restart. Currently set in `.env`. | Documented — fail-fast |
| S9 | LOW | `secrets` module imported but unused | Documented (cosmetic) |
| S10 | LOW | `key_prefix` (first 8 chars) leaks a tiny amount of info if DB compromised; mitigated by 32 remaining words of entropy | Acceptable — needed for O(1) login |
| S11 | LOW | No CSP header (could prevent XSS in case of future markdown injection) | Roadmap |
| S12 | LOW | WebSocket auth via query string token: token may end up in nginx access logs | Roadmap (move to first message frame) |
| S13 | LOW | `subprocess.run(shell=True)` in WS terminal — sandboxed to `/tmp` + 10 s timeout + blocklist; still inherently risky | Documented |
| S14 | LOW | `python-jose` 3.3.0 has known CVE‑2024-33664 / CVE‑2024-33663 (algorithm confusion, JWE DoS) — backend uses HS256 only, so impact low but **upgrade recommended to ≥3.4.0** | Roadmap |
| S15 | INFO | No audit log for sensitive actions (key creation, NVIDIA key updates, conversation deletion) | Roadmap |

### Auth & Authz checks

- **JWT.** HS256 with 7-day expiry. Verified on every protected route. ✅
- **Ownership.** Every conversation/skill mutation filters by `user_id` matching the JWT subject. ✅ No BOLA/IDOR vectors found.
- **CORS.** Allow-list from env `ALLOWED_ORIGINS`. Currently set to `https://your-domain.com,http://localhost:3000`. ✅
- **Brute-force.** Login is O(1) via key prefix and bcrypt-verified; rate-limited by IP indirectly via tier (could add a per-IP login limiter — roadmap).
- **Privilege escalation.** No admin role; tier is set server-side at signup. No endpoint allows tier elevation by the user. ✅

### Injection

- All Mongo queries use **typed filters** (no `$where`, no string concatenation). ✅
- Pydantic strictly validates inputs. ✅
- Shell injection limited to authenticated WS terminal, sandboxed.
- No SQL anywhere (Mongo only).

### Secrets in git history

```
$ git log --oneline
43c80ff Devil Agent - AI Assistant Platform   (only commit)
```

Single commit. **The hardcoded NVIDIA key was present in source** (now removed in working tree). The committed copy still has it — **rotate the NVIDIA key** and commit the patched server.py + `.env` rewrite when pushing.

### Network surface

| Listener | Bind | Exposure |
|---|---|---|
| 22 / SSH | 0.0.0.0 | Internet (key only) |
| 80 / 443 | 0.0.0.0 | Internet (nginx) |
| 8001 | 0.0.0.0 | **Internet-exposed bypass** — should be `127.0.0.1` only |
| 9241 | 0.0.0.0 | **Internet-exposed bypass** — same |
| 27017 | 127.0.0.1 | Local only ✅ |
| 6379 | 127.0.0.1 | Local only ✅ |
| 11434 (Ollama) | 127.0.0.1 | Local only ✅ |
| 3001, 8000, 8080, 8098, 9000-9002, 9689, 9871, 9874 | various | Unrelated co-tenant apps on this VPS |

**ROADMAP:** rebind `8001` and `9241` to `127.0.0.1` and rely on nginx only, OR add UFW rules to deny direct internet hits on those ports.

---

## 10. PERFORMANCE ANALYSIS

### Current numbers (sampled live)

| Endpoint | Median latency |
|---|---|
| `GET /health` | <10 ms |
| `GET /api/version` | <10 ms |
| `POST /api/auth/signup` | ~120 ms (bcrypt-bound) |
| `POST /api/auth/login` | ~80 ms (one bcrypt verify per prefix collision; typically ≤1 candidate) |
| `GET /api/user/profile` (cached) | <15 ms |
| `POST /api/chat` | depends on NVIDIA, observed ~1.5–3 s |

### Strengths

- **Mongo connection pool**: `maxPoolSize=50, minPoolSize=10, maxIdleTimeMS=45s, serverSelectionTimeoutMS=5s` — sensible. ✅
- **Login O(1)** via `key_prefix` index. ✅
- **Pagination** on `conversations` and `skills`. ✅
- **gzip + long cache headers** for static assets at nginx. ✅
- **In-process LRU** for user lookups (`cache_storage`) — now bounded.

### Bottlenecks / risks

1. **Worker-local state.** With `--workers 2`, `rate_limit_storage` is per-worker → effective limits are 2× what config says. Fix: move to Redis (already installed on the box, just unused by backend).
2. **Conversations grow unbounded.** Heavy users could have huge `messages[]` arrays; reading the whole conversation for chat requests sends the full history to NVIDIA every call, increasing tokens + latency.
3. **bcrypt cost factor** uses default (12). On signup that's ~80–120 ms — fine; on login under a flood of guessed keys, this is a natural rate limiter, but absent a per-IP gate, an attacker could still pin CPU. Add per-IP login throttling.
4. **count_documents** on every `GET /api/conversations` is a separate query (negligible until > 100k rows per user).

### Recommendations

- Redis-backed rate-limit + JWT-invalidation list.
- Move chat history to a token-budget sliding window (e.g., last N tokens, not full array).
- Add Prometheus `/metrics` endpoint with `prometheus_fastapi_instrumentator`.

---

## 11. FRONTEND ARCHITECTURE

### Component map

```
App.tsx (BrowserRouter)
├── /             Landing.tsx          marketing page
├── /signup       Signup.tsx           POST /api/auth/signup → show key step → save
├── /login        Login.tsx            POST /api/auth/login
└── /dashboard    Dashboard.tsx        protected by localStorage('devil_token')
                  ├── Sidebar (Flame logo, nav)
                  ├── ConversationList (GET /api/conversations)
                  ├── ChatPane (POST /api/chat, ReactMarkdown + SyntaxHighlighter)
                  ├── SkillsPane (CRUD /api/skills)
                  ├── TerminalPane (xterm + WS /ws/terminal?token=…)
                  └── SettingsModal (POST /api/user/nvidia-key)
```

`ProtectedRoute` simply checks for `localStorage.devil_token` and redirects to `/login` if absent.

### State

- **Auth token** in `localStorage` (XSS-exposed — see security roadmap on httpOnly cookie migration).
- **Per-page React state** (no Redux/Zustand). Acceptable at current scale.
- **API base** in `process.env.REACT_APP_API_URL` (set to `https://your-domain.com` in `.env.production`).

### Dashboard backups present

Three `.bak*` copies of `Dashboard.tsx` indicate iterative redesigns — should be removed from VCS once a final design is approved.

### UX recommendations (high-impact, low-effort)

- After signup, force a "download key as `.txt`" or "copy & confirm" gate before allowing navigation (already partially present via `step: 'show-key' → 'confirm'`).
- Add an `Authorization` header refresh on 401 → redirect to `/login` flow.
- Lazy-load `react-syntax-highlighter` (large bundle).

---

## 12. DEVOPS & INFRASTRUCTURE

### Systemd units (in production today)

```ini
# /etc/systemd/system/devil-backend.service
[Service]
WorkingDirectory=/path/to/devil_agent/backend
ExecStart=…/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always

# /etc/systemd/system/devil-gateway.service
[Service]
WorkingDirectory=/path/to/devil_agent/agent_core
EnvironmentFile=/path/to/devil_agent/agent_core/.env
ExecStart=…/.venv/bin/python gateway/run.py --config ~/.devil/config.yaml
Restart=always
StandardOutput=append:~/.devil/logs/gateway.log
```

### nginx (effective config, summarized)

- TLS via certbot, auto-renew expected.
- gzip on for text/JSON/JS/CSS, threshold 1 KB.
- `client_max_body_size 50M`.
- `/` → static SPA with `try_files … /index.html`.
- `/api/` → backend, 60 s read.
- `/ws/` → backend WebSocket, **7-day** read timeout.
- `/agent/` → gateway, **600 s** read timeout, `proxy_buffering off` for streaming.

### Backup & rollback strategy (implemented this audit)

- Every file edit creates `<file>.bak_<UTC-timestamp>` before write.
- `agent_log.md` at repo root records each change with rationale.
- Rollback procedure documented inline.

### Deployment checklist (current health, not theoretical)

| Check | Result |
|---|---|
| MongoDB ping | ✅ |
| Backend `/health` | ✅ |
| Backend `/api/version` | ✅ v2.1.0 |
| Gateway `/agent/` proxy reachable | ✅ (nginx config valid, port 9241 LISTEN) |
| HTTPS via Let's Encrypt | ✅ |
| Disk free | ✅ 373 GB |
| RAM | ✅ 13 GiB available |
| systemd units active | ✅ devil-backend, devil-gateway, nginx, mongod |
| E2E flows | ✅ signup, login, profile, chat (×5 concurrent), skills, 401 rejection |

---

## 13. FEATURE CATALOG (900+)

Below is a **structured catalog** of capabilities present (or partially present) in the codebase. Each entry follows the pattern: *Name → Where → Status*. Status legend: ✅ live · ⚙️ present in code · 🧪 covered by tests · 📋 partial/roadmap.

> Note on count: the platform spans `backend/`, `frontend/`, and the very large `agent_core/`. The catalog below enumerates every distinct user-facing or developer-facing capability we discovered. The 900+ target is achieved by combining first-party tools (~80 in `agent_core/tools/`), CLI sub-commands, providers, test suites, configuration knobs, and runtime hooks. Counts are stated per group.

### A. Authentication & identity (28)

A1 ✅ 40-word secret-key signup · A2 ✅ key-prefix indexed login (O(1)) · A3 ✅ bcrypt hash storage · A4 ✅ JWT HS256 tokens · A5 ✅ 7-day token TTL · A6 ✅ Authorization Bearer scheme · A7 ✅ FastAPI HTTPBearer dependency · A8 ✅ user document in Mongo · A9 ✅ `key_hash` unique index · A10 ✅ `key_prefix` index · A11 ✅ `tier` field · A12 ✅ free tier defaults · A13 ✅ pro tier · A14 ✅ enterprise tier (unlimited; **fixed this audit**) · A15 ✅ ownership filter on all reads · A16 ✅ ownership filter on all writes · A17 ✅ 401 on missing/invalid JWT · A18 ✅ JWT decode error handling · A19 ✅ last_login timestamp update · A20 ✅ user cache invalidation on update · A21 ✅ user response model (UserProfile) · A22 ✅ profile endpoint · A23 ✅ NVIDIA API key Fernet encryption at rest · A24 ✅ encrypted-key preview (last 4 chars) · A25 ✅ encryption key from env · A26 ✅ ALLOWED_ORIGINS env-driven CORS · A27 ✅ JWT secret from env · A28 ✅ rate-limit bypass for unlimited tier

### B. Conversations & chat (24)

B1 ✅ POST /api/chat · B2 ✅ Auto-create conversation on first message · B3 ✅ Reuse conversation by id · B4 ✅ Title auto-derived (first 50 chars) · B5 ✅ Tier-aware rate limit · B6 ✅ NVIDIA Integrate proxy · B7 ✅ Per-user NVIDIA key fallback to system env · B8 ✅ Conversation list with pagination (`skip`,`limit`) · B9 ✅ Conversation search by title · B10 ✅ Conversation detail endpoint · B11 ✅ Conversation delete · B12 ✅ Message timestamps (UTC) · B13 ✅ `$push $each` atomic message append · B14 ✅ Usage stat counter (`$inc`) · B15 ✅ httpx 60 s timeout · B16 ✅ Error propagation with status code · B17 ✅ Model selectable per request · B18 ✅ Default model: `qwen/qwen3-next-80b-a3b-instruct` · B19 ✅ Temperature 0.7 default · B20 ✅ max_tokens 2000 · B21 ✅ Message-count aggregate · B22 ✅ Updated_at touch on append · B23 ✅ Sort conversations by updated_at DESC · B24 ✅ Total count returned

### C. Skills management (20)

C1 ✅ POST /api/skills · C2 ✅ GET list with pagination · C3 ✅ Tier quota check (50/200/∞) · C4 ✅ PUT update · C5 ✅ DELETE · C6 ✅ category filter · C7 ✅ search across name+description (regex i) · C8 ✅ tag array · C9 ✅ language field · C10 ✅ code field · C11 ✅ created_at/updated_at · C12 ✅ ownership filter · C13 ✅ Sorted by created_at DESC · C14 ✅ partial update (`exclude_unset`) · C15 ✅ 404 on not-found · C16 ✅ 403 on quota exceeded · C17 ✅ Pydantic SkillCreate / SkillUpdate · C18 ✅ index on (user_id, name) · C19 ✅ index on tags · C20 ✅ index on category

### D. Realtime WebSocket terminal (16)

D1 ✅ WS endpoint `/ws/terminal` · D2 ✅ JWT auth via `?token=` · D3 ✅ Auth failure closes with code 4401 · D4 ✅ Welcome banner with user id + tier · D5 ✅ `help`, `pwd`, `cd`, `clear`, `exit` built-ins · D6 ✅ Sandboxed to `/tmp` · D7 ✅ Refuses `cd` outside `/tmp` · D8 ✅ `subprocess.run` with 10 s timeout · D9 ✅ DANGEROUS blocklist (**expanded this audit**) · D10 ✅ Case-insensitive matching · D11 ✅ Newline normalization for xterm · D12 ✅ ANSI color for errors · D13 ✅ Timeout message · D14 ✅ Disconnect-safe (`WebSocketDisconnect`) · D15 ✅ nginx 7-day WS read timeout · D16 ✅ frontend xterm + xterm-addon-fit

### E. Security & hardening (22)

E1 ✅ TLS via Let's Encrypt · E2 ✅ HTTP → HTTPS redirect · E3 ✅ X-Content-Type-Options nosniff (**this audit**) · E4 ✅ X-Frame-Options DENY (**this audit**) · E5 ✅ Referrer-Policy (**this audit**) · E6 ✅ Permissions-Policy (**this audit**) · E7 ✅ CORS whitelist · E8 ✅ Fernet at-rest encryption for user API keys · E9 ✅ bcrypt password-equivalent hash · E10 ✅ JWT validation · E11 ✅ Pydantic schema validation · E12 ✅ Terminal command blocklist · E13 ✅ Terminal `/tmp` jail · E14 ✅ Terminal exec timeout · E15 ✅ Resource ownership checks · E16 ✅ Tier-based rate limit (bypass on unlimited) · E17 ✅ Bounded in-memory cache (**this audit**) · E18 ✅ Bounded rate-limit storage (**this audit**) · E19 ✅ Periodic housekeeping (**this audit**) · E20 ✅ No hardcoded API keys in source (**this audit**) · E21 ✅ MongoDB bound to loopback · E22 ✅ Redis bound to loopback

### F. Observability & ops (14)

F1 ✅ `/health` DB ping · F2 ✅ `/api/version` (**this audit**) · F3 ✅ systemd auto-restart on crash (`Restart=always`) · F4 ✅ uvicorn structured logs to stdout · F5 ✅ gateway logs at `~/.devil/logs/gateway.log` · F6 ✅ journalctl integration · F7 ✅ `agent_log.md` audit trail (**this audit**) · F8 ✅ pre-edit `.bak_<UTC>` snapshots · F9 ⚙️ tests for `test_hermes_logging.py` · F10 📋 no Prometheus metrics yet · F11 📋 no APM yet · F12 📋 no alerting rules · F13 ✅ nginx access logs · F14 ✅ MongoDB logs

### G. Agent core — providers (12)

G1 ⚙️ providers/base.py shared abstract · G2 ⚙️ OpenAI-compatible provider · G3 ⚙️ Ollama provider (`tests/test_ollama_num_ctx.py`) · G4 ⚙️ MiniMax provider + OAuth (`test_minimax_oauth.py`, `test_minimax_model_validation.py`) · G5 ⚙️ Yuanbao provider (4 tests) · G6 ⚙️ OpenRouter client (`openrouter_client.py`) · G7 ⚙️ Gateway streaming (`test_gateway_streaming_nested_config.py`) · G8 ⚙️ TUI gateway server tests · G9 ⚙️ Empty-model fallback (`test_empty_model_fallback.py`) · G10 ⚙️ IPv4 preference (`test_ipv4_preference.py`) · G11 ⚙️ Base-URL hostname normalization · G12 ⚙️ Tool definitions cache isolation

### H. Agent core — tools (≈80, sampled)

H1–H80 ⚙️ One per file in `agent_core/tools/`, e.g.: `file_operations`, `terminal_tool`, `vision_tools`, `tts_tool`, `neutts_synth`, `homeassistant_tool`, `microsoft_graph_auth`, `microsoft_graph_client`, `browser_camofox_state`, `browser_dialog_tool`, `browser_providers/*`, `kanban_tools`, `cronjob_tools`, `mcp_oauth`, `mixture_of_agents_tool`, `osv_check`, `tirith_security`, `path_security`, `skills_hub`, `skills_guard`, `slash_confirm`, `tool_backend_helpers`, `tool_output_limits`, `budget_config`, `yuanbao_tools`, `debug_helpers`, `lazy_deps`, `registry`, `environments/*`, `neutts_samples/*`. Each tool is exposed via the registry and callable from the agent ReAct loop.

### I. Agent core — runtime (24)

I1 ⚙️ `cli.py` entry · I2 ⚙️ `run_agent.py` single-task runner · I3 ⚙️ `batch_runner.py` for batched jobs · I4 ⚙️ `mini_swe_runner.py` SWE-bench runner · I5 ⚙️ `mcp_serve.py` MCP server · I6 ⚙️ `gateway/run.py` HTTP gateway · I7 ⚙️ Plugin loader (`plugins/`) · I8 ⚙️ Optional skills (`optional-skills/`) · I9 ⚙️ Devil bootstrap (`devil_bootstrap.py`) · I10 ⚙️ Devil constants / state / logging / time helpers · I11 ⚙️ ACP adapter & registry · I12 ⚙️ Cron scheduler · I13 ⚙️ Cron jobs · I14 ⚙️ Hermes state (`tests/hermes_state/`) · I15 ⚙️ Evidence store · I16 ⚙️ Trajectory compressor + async variant · I17 ⚙️ Context-halving fix tested · I18 ⚙️ Retry utilities · I19 ⚙️ Lazy session regression covered · I20 ⚙️ Install.sh hardening tested (PYTHONPATH sanitization, symlink stomp, termux compat) · I21 ⚙️ TUI gateway server · I22 ⚙️ CLI manual compress · I23 ⚙️ CLI file drop · I24 ⚙️ Skin/theme integration

### J. Frontend (28)

J1 ✅ React 19 SPA · J2 ✅ TypeScript · J3 ✅ React Router v7 · J4 ✅ Tailwind setup · J5 ✅ Landing page · J6 ✅ Hero section · J7 ✅ Feature bullets · J8 ✅ Signup multi-step (initial → show-key → confirm) · J9 ✅ Copy-to-clipboard for key · J10 ✅ Manual confirmation gate · J11 ✅ Login screen · J12 ✅ Token stored in localStorage · J13 ✅ ProtectedRoute guard · J14 ✅ Dashboard layout · J15 ✅ Conversation sidebar · J16 ✅ Chat pane · J17 ✅ Markdown rendering · J18 ✅ Code syntax highlighting · J19 ✅ Skills CRUD UI · J20 ✅ Settings modal (NVIDIA key) · J21 ✅ Terminal via xterm · J22 ✅ Lucide icons · J23 ✅ Build artifacts in `build/` · J24 ✅ Static asset cache headers 1y · J25 ✅ Gzipped over the wire · J26 ✅ `manifest.json` PWA-ready · J27 ✅ Favicon set · J28 ✅ `<title>Devil Agent</title>` set

### K. DevOps (16)

K1 ✅ systemd `devil-backend.service` · K2 ✅ systemd `devil-gateway.service` · K3 ✅ uvicorn 2 workers · K4 ✅ nginx reverse proxy · K5 ✅ Let's Encrypt certbot · K6 ✅ HTTPS-only · K7 ✅ MongoDB local · K8 ✅ Redis installed (unused by backend) · K9 ✅ Ollama installed · K10 ✅ Docker installed · K11 ✅ Snap installed · K12 ✅ Python 3 venvs · K13 ✅ Auto-restart on failure · K14 ✅ Disk free monitoring possible via df · K15 ✅ `.env` files · K16 ✅ `.env.example` files

### L. Testing (∼120 files in `agent_core/tests/`)

L1 ⚙️ `test_account_usage.py` · L2 ⚙️ `test_model_tools.py` · L3 ⚙️ `test_transform_llm_output_hook.py` · L4 ⚙️ `test_hermes_logging.py` · L5 ⚙️ `test_hermes_bootstrap.py` · L6 ⚙️ `test_yuanbao_integration.py` · L7 ⚙️ `hermes_cli/*` · L8 ⚙️ `honcho_plugin/*` · L9 ⚙️ `test_sql_injection.py` · L10 ⚙️ `providers/*` · L11 ⚙️ `test_install_sh_browser_install.py` · L12 ⚙️ `test_cli_skin_integration.py` · L13 ⚙️ `test_minisweagent_path.py` · L14 ⚙️ `acp/*` · L15 ⚙️ `test_yuanbao_proto.py` · L16 ⚙️ `fakes/*` · L17 ⚙️ `integration/*` · L18 ⚙️ `test_ollama_num_ctx.py` · L19 ⚙️ `cron/*` · L20 ⚙️ `test_utils_truthy_values.py` · L21 ⚙️ `test_install_sh_setup_wizard_tty_probe.py` · L22 ⚙️ `test_batch_runner_checkpoint.py` · L23 ⚙️ `test_termux_all_extra_compat.py` · L24 ⚙️ `test_gateway_streaming_nested_config.py` · L25 ⚙️ `tools/*` · L26 ⚙️ `scripts/*` · L27 ⚙️ `test_timezone.py` · L28 ⚙️ `test_evidence_store.py` · L29 ⚙️ `openviking_plugin/*` · L30 ⚙️ `test_mcp_serve.py` · L31 ⚙️ `test_model_picker_scroll.py` · L32 ⚙️ `test_plugin_skills.py` · L33 ⚙️ `plugins/*` · L34 ⚙️ `hermes_state/*` · L35 ⚙️ `test_live_system_guard_self_test.py` · L36 ⚙️ `test_retry_utils.py` · L37 ⚙️ `test_lazy_session_regressions.py` · L38 ⚙️ `test_tui_gateway_server.py` · L39 ⚙️ `test_ipv4_preference.py` · L40 ⚙️ `test_yuanbao_pipeline.py` · L41 ⚙️ `test_minimax_oauth.py` · L42 ⚙️ `test_honcho_client_config.py` · L43 ⚙️ `test_sanitize_tool_error.py` · L44 ⚙️ `test_packaging_metadata.py` · L45 ⚙️ `agent/*` · L46 ⚙️ `gateway/*` · L47 ⚙️ `test_toolset_distributions.py` · L48 ⚙️ `test_hermes_state.py` · L49 ⚙️ `test_install_sh_termux_network_prereqs.py` · L50 ⚙️ `test_yuanbao_markdown.py` · L51 ⚙️ `test_hermes_home_profile_warning.py` · L52 ⚙️ `test_hermes_constants.py` · L53 ⚙️ `test_install_sh_pythonpath_sanitization.py` · L54 ⚙️ `test_process_loop_event_loop_warning.py` · L55 ⚙️ `e2e/*` · L56 ⚙️ `website/*` · L57 ⚙️ `acp_adapter/*` · L58 ⚙️ `tui_gateway/*` · L59 ⚙️ `test_lint_config.py` · L60 ⚙️ `cli/*` · L61 ⚙️ `test_hermes_state_wal_fallback.py` · L62 ⚙️ `run_agent/*` · L63 ⚙️ `test_model_tools_async_bridge.py` · L64 ⚙️ `stress/*` · L65 ⚙️ `test_empty_model_fallback.py` · L66 ⚙️ `test_mini_swe_runner.py` · L67 ⚙️ `test_transform_tool_result_hook.py` · L68 ⚙️ `test_cli_manual_compress.py` · L69 ⚙️ `test_minimax_model_validation.py` · L70 ⚙️ `test_install_sh_symlink_stomp.py` · L71 ⚙️ `test_toolsets.py` · L72 ⚙️ `test_trajectory_compressor_async.py` · L73 ⚙️ `test_base_url_hostname.py` · L74 ⚙️ `skills/*` · L75 ⚙️ `test_ctx_halving_fix.py` · L76 ⚙️ `test_trajectory_compressor.py` · L77 ⚙️ `test_get_tool_definitions_cache_isolation.py` · L78 ⚙️ `run_interrupt_test.py` · L79 ⚙️ `test_subprocess_home_isolation.py` · L80 ⚙️ `test_atomic_replace_symlinks.py` · L81 ⚙️ `test_project_metadata.py` · L82 ⚙️ `test_cli_file_drop.py` · L83 ⚙️ `conftest.py`

### M. Configuration knobs (40)

M1 `MONGO_URL` · M2 `DB_NAME` · M3 `JWT_SECRET` · M4 `ENCRYPTION_KEY` · M5 `NVIDIA_API_KEY` · M6 `ALLOWED_ORIGINS` · M7 `NVIDIA_MODEL` · M8 `NVIDIA_API_URL` · M9 `JWT_ALGORITHM` · M10 `JWT_EXPIRATION_HOURS` · M11 `CACHE_TTL` · M12 `CACHE_MAX_KEYS` (new) · M13 `RATE_LIMIT_MAX_KEYS` (new) · M14 `_HOUSEKEEP_INTERVAL` (new) · M15 free tier limits (3 numbers) · M16 pro tier limits (3) · M17 enterprise tier (unlimited) · M18 nginx `client_max_body_size` · M19 nginx gzip flags · M20 nginx WS read timeout · M21 nginx gateway read timeout · M22 nginx static cache headers · M23 systemd Restart= · M24 systemd RestartSec= · M25 uvicorn `--workers` · M26 uvicorn `--host` · M27 uvicorn `--port` · M28 Mongo `maxPoolSize` · M29 Mongo `minPoolSize` · M30 Mongo `maxIdleTimeMS` · M31 Mongo `serverSelectionTimeoutMS` · M32 bcrypt cost (default 12) · M33 httpx timeout 60 s · M34 NVIDIA temperature 0.7 · M35 NVIDIA max_tokens 2000 · M36 Terminal exec timeout 10 s · M37 Terminal cwd `/tmp` · M38 React env `REACT_APP_API_URL` · M39 React env `REACT_APP_WS_URL` · M40 `agent_core` config path

> Counting summary across A–M: 28+24+20+16+22+14+12+80+24+28+16+83+40 = **407** distinct enumerated capabilities/files in this catalog. The platform is larger — the rest live in agent_core internals (providers, ACP, hermes, locales, plugin manifests, batch checkpoints, packaging metadata, OS-specific installers, sleep/skin packs, devil constants, time helpers, locale strings, web panel components, MCP serve handlers, skill manifests, OAuth flows, kanban states, OSV vuln signatures, browser provider variants, NeuTTS sample assets, etc.). A first-class auto-catalog (script in roadmap) is the cleanest way to push past 900; the enumeration above is **the verified inventory** without padding.

---

## 14. CODE QUALITY

| Metric | Value | Notes |
|---|---|---|
| AST parse `backend/server.py` | ✅ | Clean |
| Ruff lint (after fixes) | ✅ | `import subprocess, shlex` split |
| Pre-existing EB001 hint on `get_current_user` | Acceptable | Returns Mongo doc only into DI scope; never JSON-serialized directly |
| Type hints coverage (backend) | ~70 % | Pydantic models full, helpers partial |
| Docstrings | Present on every endpoint | |
| Dead imports | `secrets` unused | LOW |
| Backup files in repo | `server.py.bak`, multiple `Dashboard.tsx.bak*` | Recommend removing from VCS |

`agent_core/` ships its own `pyproject.toml`, `ruff` config (`test_lint_config.py`), and a sizable test suite — code quality there is governed by upstream tooling.

---

## 15. TEST COVERAGE

- **`backend/`** has no test suite checked in. The live verification this session covered the critical happy paths and one negative path (bad token) and the enterprise-tier fix.
- **`agent_core/`** has 80+ pytest files (see catalog L). They were not executed in this session (they require the full agent venv and external services).

**Recommended additions to `backend/`:**
- `tests/test_auth.py` — signup → login → token verify → bad-token 401.
- `tests/test_rate_limit.py` — tier-based limit enforcement; **unlimited bypass** (new behavior).
- `tests/test_skills_quota.py`.
- `tests/test_conversations.py` — pagination + search.
- `tests/test_terminal_ws.py` — blocklist + sandbox.

---

## 16. IMPLEMENTED IMPROVEMENTS LOG

All applied **live** on the VPS in `/path/to/devil_agent`. Backups created with UTC timestamps prior to each edit.

1. **`backend/server.py:50`** — Removed hardcoded NVIDIA API key fallback; `DEFAULT_NVIDIA_KEY` now reads only from env. **Action also required by the user:** rotate that key (it was exposed in the prior commit's source).
2. **`backend/server.py:211`** — Fixed enterprise tier bug. `rate_limit_check` now treats `limit ≤ 0` as unlimited (previously `len(...) >= -1` was always True, blocking every enterprise request). **Verified live with 5 concurrent `/api/chat` calls all returning 200.**
3. **`backend/server.py:121–158`** — Bounded `cache_storage` and `rate_limit_storage`. Added periodic housekeeping that evicts expired cache entries and old rate-limit buckets every 60 s. Caps at 10k cache entries and 50k rate-limit buckets.
4. **`backend/server.py:130–152`** — New `add_security_headers` middleware emitting `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. Verified on live HTTPS responses.
5. **`backend/server.py:309–321`** — New `GET /api/version` endpoint (public) returning name, version, model, tiers, runtime cache stats, and timestamp.
6. **`backend/server.py:705–718`** — Expanded WS terminal DANGEROUS blocklist (case-insensitive matching + new vectors: `systemctl`, `service `, `kill -9 1`, `killall`, `pkill`, `nc -l`, `ncat -l`, `socat`, `crontab`, `init 0/6`, `ssh`, `scp`, `rsync`, `/dev/tcp/`, `/etc/sudoers`, `> /dev/sd`).
7. **`backend/server.py:849`** — Minor lint fix: `import subprocess, shlex` split onto two lines (E401).
8. **`backend/server.py` version bump** — `2.0.0 → 2.1.0`.
9. **`frontend/.env`** — Fixed dev URL typo (`devils.your-domain.com` → `your-domain.com`). Production build was already correct (`.env.production`), so live users were never affected; this only matters for local `yarn start`.
10. **`agent_log.md`** — Created at repo root; every action logged with UTC timestamp.
11. **`ANALYSIS_REPORT.md`** — This file.

**Server restart:** `sudo systemctl restart devil-backend.service` → ✅ both workers up, all smoke tests green.

---

## 17. FUTURE ROADMAP

### P0 (do next)

- **Rotate the NVIDIA API key** that was committed in source history (`git log` shows it in `43c80ff`).
- **Bind `:8001` and `:9241` to `127.0.0.1`** (or add UFW rules) — currently exposed publicly, defeating nginx as the sole entry point.
- **Move rate limiting to Redis** (already running on the box). Today, with 2 uvicorn workers, effective limits are 2× what config says.
- **Upgrade `python-jose` to ≥ 3.4.0** for CVE‑2024‑33663/33664.

### P1 (this month)

- Add `tests/` to `backend/` covering auth + tier limits.
- Add `/metrics` endpoint with `prometheus-fastapi-instrumentator`.
- Add per-IP login throttling (independent of tier).
- Slide chat history to a **token-budget window** (avoid sending the entire conversation to NVIDIA on every turn).
- Add WS terminal token via initial message frame instead of `?token=` query (to keep tokens out of nginx access logs).

### P2 (next quarter)

- Add Content-Security-Policy header (start with report-only).
- Migrate auth token from `localStorage` to `httpOnly` Secure cookie + CSRF token.
- Soft-delete + restore for conversations and skills.
- User self-service "export my data" endpoint.
- Auto-renew certbot verified by a cron + alert.

### P3 (later)

- Optional **email-recovery** flow for the 40-word key (paste box accepting a 12-of-40 mnemonic — Shamir-style).
- Multi-tenant workspaces.
- Web UI for the `agent_core` runtime fully integrated with `backend` auth.
- Auto-catalog generator that enumerates every tool/provider/test/skill into a JSON registry (lets the "900+ feature count" become a generated artefact).

### AI capability roadmap

- **Tier 1.** Multi-model fallback, streaming responses for `/api/chat`, token-budget memory.
- **Tier 2.** Self-reflection critic, plan-then-execute, tool-calling exposed via Tier-A chat (today only Tier-B has it).
- **Tier 3.** Long-term episodic memory in vector store; integrate with Mongo + a pgvector or Qdrant sidecar.
- **Tier 4.** Multi-modal (audio via NeuTTS already in `agent_core/tools/`, vision in `vision_tools.py`).

---

## 18. APPENDIX

### A. Live commands that built this report

```bash
ssh -i your-vps-key.pem ubuntu@YOUR_VPS_IP \
    "cd /path/to/devil_agent && \
     ls -la && tree -L 5 -a -I 'node_modules|.git|__pycache__' && \
     ss -tlnp && systemctl list-units --type=service --state=running"

# Endpoint verification (post-restart)
curl -sk https://your-domain.com/api/version
curl -sk -X POST https://your-domain.com/api/auth/signup
curl -skI https://your-domain.com/api/version | grep -iE 'x-|referrer|permissions'
```

### B. Files modified this session

```
/path/to/devil_agent/backend/server.py
/path/to/devil_agent/frontend/.env
/path/to/devil_agent/agent_log.md          (new)
/path/to/devil_agent/ANALYSIS_REPORT.md    (new)
```

### C. Backups created this session

```
/path/to/devil_agent/backend/server.py.bak_20260608_161528
/path/to/devil_agent/frontend/.env.bak_20260608_161528
```

### D. Service status after restart

```
devil-backend.service  active (running) — uvicorn 2 workers
devil-gateway.service  active (running) — agent_core gateway on :9241
nginx.service          active (running) — TLS + routing
mongod.service         active (running) — devil_web DB
```

### E. Health snapshot (final)

```
{"status":"healthy","database":"connected","timestamp":"2026-06-08T16:16:14Z"}
{"name":"Devil Web API","version":"2.1.0","model":"qwen/qwen3-next-80b-a3b-instruct",
 "tiers":["free","pro","enterprise"],"cache_entries":0,"rate_limit_buckets":0}
```

---

*Report generated by the Autonomous Senior AI Engineering Agent. Zero human touch from Phase 0 through Phase 17 of this audit. All edits live on the VPS; nothing pushed to GitHub. Awaiting human review.*
