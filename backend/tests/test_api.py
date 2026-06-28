"""
Smoke tests for Devil Web API (v2.2.0).
Run from /home/ubuntu/devil_agent/backend with venv active:
    python -m pytest tests/test_api.py -v
"""
import os
import sys
import asyncio
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mcp_module  # noqa: E402


def test_registry_has_core_tools():
    names = {t["name"] for t in mcp_module.list_tools()}
    for n in ("echo", "now", "uuid", "hash", "calc", "fs_write", "fs_read", "fs_list", "fs_delete", "shell", "http_fetch", "json_parse"):
        assert n in names, f"Missing tool: {n}"


def test_servers_listed():
    servers = mcp_module.list_servers()
    cats = {s["name"] for s in servers}
    assert {"filesystem", "math", "network", "system", "utility"}.issubset(cats)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if not hasattr(asyncio, "run") else asyncio.run(coro)


def test_echo_tool():
    res = _run(mcp_module.execute_tool("echo", {"text": "ping"}))
    assert res["ok"] is True
    assert res["result"] == {"echo": "ping"}


def test_calc_tool():
    res = _run(mcp_module.execute_tool("calc", {"expression": "(2+3)*4"}))
    assert res["ok"] is True
    assert res["result"]["value"] == 20


def test_calc_rejects_unsafe():
    res = _run(mcp_module.execute_tool("calc", {"expression": "__import__('os')"}))
    assert res["ok"] is False


def test_fs_roundtrip():
    w = _run(mcp_module.execute_tool("fs_write", {"path": "test/hello.txt", "content": "hi"}))
    assert w["ok"]
    r = _run(mcp_module.execute_tool("fs_read", {"path": "test/hello.txt"}))
    assert r["ok"] and r["result"]["content"] == "hi"
    d = _run(mcp_module.execute_tool("fs_delete", {"path": "test/hello.txt"}))
    assert d["ok"]


def test_fs_no_traversal():
    res = _run(mcp_module.execute_tool("fs_write", {"path": "../escape.txt", "content": "x"}))
    assert res["ok"] is False


def test_shell_blocks_dangerous():
    res = _run(mcp_module.execute_tool("shell", {"command": "sudo rm -rf /"}))
    assert res["ok"] is False


def test_shell_runs_safe():
    res = _run(mcp_module.execute_tool("shell", {"command": "echo ok"}))
    assert res["ok"] is True
    assert "ok" in res["result"]["stdout"]


def test_unknown_tool():
    res = _run(mcp_module.execute_tool("does_not_exist", {}))
    assert res["ok"] is False
