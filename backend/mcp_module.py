"""
MCP (Model Context Protocol) Module for Devil Agent
====================================================
Sandboxed, in-process tool registry exposing safe capabilities to chat clients.

Design notes
------------
* No external `mcp` package required — this is a self-contained registry
  that follows the MCP shape (tools have a `name`, `description`,
  `input_schema`, and `execute()`).
* Every tool is sandboxed: filesystem ops are jailed under /tmp/mcp_sandbox,
  shell commands are blocked against a deny-list and time-boxed, and HTTP
  fetches go through a strict allow-list of schemes + size limits.
* Tools are pure-async so the FastAPI event loop never blocks.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import httpx

# --------------------------------------------------------------------------- #
# Sandbox setup
# --------------------------------------------------------------------------- #
MCP_SANDBOX = "/tmp/mcp_sandbox"
os.makedirs(MCP_SANDBOX, exist_ok=True)

MAX_FILE_BYTES = 1 * 1024 * 1024  # 1 MiB
MAX_HTTP_BYTES = 2 * 1024 * 1024  # 2 MiB
HTTP_TIMEOUT_S = 15
SHELL_TIMEOUT_S = 8

DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf /*", ":(){", "mkfs", "dd if=", "shutdown", "reboot",
    "halt", "poweroff", "/etc/passwd", "/etc/shadow", "/etc/sudoers",
    "sudo ", "su ", "useradd", "userdel", "usermod", "passwd",
    "iptables", "ufw ", "fdisk", "parted", "nc -l", "ncat -l", "socat",
    "crontab", "systemctl", "service ", "kill -9 1", "killall", "pkill",
    "ssh ", "scp ", "rsync ", "/dev/tcp/", "> /dev/sd",
]


def _safe_path(rel: str) -> str:
    """Resolve a path inside the sandbox. Refuses traversal."""
    rel = (rel or "").lstrip("/")
    full = os.path.realpath(os.path.join(MCP_SANDBOX, rel))
    if not full.startswith(os.path.realpath(MCP_SANDBOX)):
        raise ValueError("Path escapes sandbox")
    return full


# --------------------------------------------------------------------------- #
# Tool dataclass + registry
# --------------------------------------------------------------------------- #
@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Any]
    category: str = "general"
    danger: str = "safe"  # safe | low | medium | high
    examples: List[Dict[str, Any]] = field(default_factory=list)

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        started = time.time()
        try:
            result = await self.handler(**(params or {}))
            return {
                "ok": True,
                "tool": self.name,
                "result": result,
                "elapsed_ms": int((time.time() - started) * 1000),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "tool": self.name,
                "error": str(e),
                "elapsed_ms": int((time.time() - started) * 1000),
                "ts": datetime.now(timezone.utc).isoformat(),
            }


# --------------------------------------------------------------------------- #
# Tool implementations
# --------------------------------------------------------------------------- #
async def _t_echo(text: str = "") -> Dict[str, Any]:
    return {"echo": text}


async def _t_now() -> Dict[str, Any]:
    return {"utc": datetime.now(timezone.utc).isoformat(), "unix": time.time()}


async def _t_fs_write(path: str, content: str) -> Dict[str, Any]:
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError(f"Content exceeds {MAX_FILE_BYTES} bytes")
    full = _safe_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return {"path": path, "bytes": len(content)}


async def _t_fs_read(path: str) -> Dict[str, Any]:
    full = _safe_path(path)
    size = os.path.getsize(full)
    if size > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds {MAX_FILE_BYTES} bytes")
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        return {"path": path, "content": f.read(), "bytes": size}


async def _t_fs_list(path: str = "") -> Dict[str, Any]:
    full = _safe_path(path) if path else MCP_SANDBOX
    if not os.path.isdir(full):
        raise ValueError("Not a directory")
    items = []
    for name in sorted(os.listdir(full)):
        p = os.path.join(full, name)
        items.append({
            "name": name,
            "type": "dir" if os.path.isdir(p) else "file",
            "size": os.path.getsize(p) if os.path.isfile(p) else None,
        })
    return {"path": path or "/", "items": items}


async def _t_fs_delete(path: str) -> Dict[str, Any]:
    full = _safe_path(path)
    if os.path.isdir(full):
        shutil.rmtree(full)
    elif os.path.isfile(full):
        os.remove(full)
    else:
        raise ValueError("Not found")
    return {"deleted": path}


async def _t_shell(command: str) -> Dict[str, Any]:
    low = (command or "").lower()
    if not low.strip():
        raise ValueError("Empty command")
    if any(d in low for d in DANGEROUS_PATTERNS):
        raise ValueError("Dangerous command blocked")
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=MCP_SANDBOX,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=SHELL_TIMEOUT_S)
    except asyncio.TimeoutError:
        proc.kill()
        raise ValueError(f"Command exceeded {SHELL_TIMEOUT_S}s timeout")
    return {
        "exit_code": proc.returncode,
        "stdout": (out or b"").decode("utf-8", errors="replace")[:16000],
        "stderr": (err or b"").decode("utf-8", errors="replace")[:8000],
    }


async def _t_http_fetch(url: str, method: str = "GET") -> Dict[str, Any]:
    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValueError("Only http/https URLs allowed")
    method = (method or "GET").upper()
    if method not in ("GET", "HEAD"):
        raise ValueError("Only GET/HEAD allowed")
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S, follow_redirects=True) as cli:
        r = await cli.request(method, url)
        body = r.content[:MAX_HTTP_BYTES]
        return {
            "status": r.status_code,
            "headers": dict(r.headers),
            "body_preview": body.decode("utf-8", errors="replace")[:8000],
            "bytes": len(body),
            "truncated": len(r.content) > MAX_HTTP_BYTES,
        }


async def _t_calc(expression: str) -> Dict[str, Any]:
    # Safe math eval — only numeric + operators
    allowed = set("0123456789.+-*/(). %eE_")
    if any(c not in allowed for c in expression):
        raise ValueError("Only numbers and + - * / ( ) % allowed")
    try:
        value = eval(expression, {"__builtins__": {}}, {})  # noqa: S307 (controlled)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Invalid expression: {e}")
    return {"expression": expression, "value": value}


async def _t_json_parse(text: str) -> Dict[str, Any]:
    try:
        return {"parsed": json.loads(text)}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


async def _t_uuid() -> Dict[str, Any]:
    import uuid
    return {"uuid": str(uuid.uuid4())}


async def _t_hash(text: str, algo: str = "sha256") -> Dict[str, Any]:
    import hashlib
    algo = algo.lower()
    if algo not in ("sha256", "sha1", "md5", "sha512"):
        raise ValueError("Algo must be sha256, sha1, md5, sha512")
    h = hashlib.new(algo)
    h.update(text.encode("utf-8"))
    return {"algo": algo, "digest": h.hexdigest()}


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
REGISTRY: Dict[str, MCPTool] = {}


def _register(t: MCPTool) -> None:
    REGISTRY[t.name] = t


def _bootstrap() -> None:
    if REGISTRY:
        return
    _register(MCPTool(
        name="echo", category="utility", danger="safe",
        description="Echo text back. Useful for testing the MCP pipeline.",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        handler=_t_echo,
        examples=[{"text": "hello world"}],
    ))
    _register(MCPTool(
        name="now", category="utility", danger="safe",
        description="Get current UTC timestamp.",
        input_schema={"type": "object", "properties": {}},
        handler=_t_now,
    ))
    _register(MCPTool(
        name="uuid", category="utility", danger="safe",
        description="Generate a random v4 UUID.",
        input_schema={"type": "object", "properties": {}},
        handler=_t_uuid,
    ))
    _register(MCPTool(
        name="hash", category="utility", danger="safe",
        description="Compute a cryptographic hash of text.",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}, "algo": {"type": "string"}},
            "required": ["text"],
        },
        handler=_t_hash,
    ))
    _register(MCPTool(
        name="calc", category="math", danger="safe",
        description="Evaluate a numeric arithmetic expression (no variables/functions).",
        input_schema={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
        handler=_t_calc,
        examples=[{"expression": "(2+3)*7"}],
    ))
    _register(MCPTool(
        name="json_parse", category="utility", danger="safe",
        description="Parse a JSON string and return the parsed value.",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        handler=_t_json_parse,
    ))
    _register(MCPTool(
        name="fs_write", category="filesystem", danger="low",
        description="Write a UTF-8 text file inside the MCP sandbox (/tmp/mcp_sandbox).",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
        handler=_t_fs_write,
    ))
    _register(MCPTool(
        name="fs_read", category="filesystem", danger="low",
        description="Read a UTF-8 text file inside the MCP sandbox.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=_t_fs_read,
    ))
    _register(MCPTool(
        name="fs_list", category="filesystem", danger="safe",
        description="List files in a directory inside the MCP sandbox.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=_t_fs_list,
    ))
    _register(MCPTool(
        name="fs_delete", category="filesystem", danger="medium",
        description="Delete a file or directory inside the MCP sandbox.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=_t_fs_delete,
    ))
    _register(MCPTool(
        name="shell", category="system", danger="high",
        description="Run a shell command inside the MCP sandbox. Deny-listed, time-boxed at 8s.",
        input_schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        handler=_t_shell,
    ))
    _register(MCPTool(
        name="http_fetch", category="network", danger="medium",
        description="Fetch a public HTTP/HTTPS URL (GET/HEAD only, 2 MiB cap, 15s timeout).",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "method": {"type": "string"}},
            "required": ["url"],
        },
        handler=_t_http_fetch,
    ))


    # Load extra pure-compute tools (extra-tool handlers take a dict; wrap to **kwargs)
    def _wrap(h):
        async def _w(**kwargs):
            return await h(kwargs)
        return _w
    try:
        from mcp_extra_tools import EXTRA_TOOLS
        for name, cat, danger, desc, schema, handler in EXTRA_TOOLS:
            if name not in REGISTRY:
                _register(MCPTool(name=name, category=cat, danger=danger,
                                  description=desc, input_schema=schema, handler=_wrap(handler)))
    except Exception as _e:
        print(f"[mcp] failed to load extra tools: {_e}")

def list_tools() -> List[Dict[str, Any]]:
    _bootstrap()
    return [
        {
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "danger": t.danger,
            "input_schema": t.input_schema,
            "examples": t.examples,
        }
        for t in REGISTRY.values()
    ]


async def execute_tool(name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _bootstrap()
    tool = REGISTRY.get(name)
    if not tool:
        return {"ok": False, "error": f"Unknown tool: {name}"}
    return await tool.execute(params or {})


def list_servers() -> List[Dict[str, Any]]:
    """Return the set of available logical MCP 'servers' (categories)."""
    _bootstrap()
    by_cat: Dict[str, int] = {}
    for t in REGISTRY.values():
        by_cat[t.category] = by_cat.get(t.category, 0) + 1
    return [
        {"name": cat, "tool_count": cnt, "status": "active"}
        for cat, cnt in sorted(by_cat.items())
    ]


# Auto-bootstrap on import
_bootstrap()
