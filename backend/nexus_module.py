"""
NEXUS Autonomous Engineering Operating System — Backend Module
v1.0 — Production Build

Implements the in-process layer for:
  - Strategic Briefs (Layer 1)
  - Task Graph plans (Layer 2)
  - Execution Log (Layer 3 audit)
  - Sentinel scans (Layer 4 — secrets / OWASP heuristics)
  - Decision Records (ADRs)
  - Failure Pattern Library
  - Project Genome (live state object)

All data is persisted to MongoDB collections prefixed with nexus_*.
Pure-Python; no extra dependencies beyond pymongo (already installed).
"""
from __future__ import annotations

import hashlib
import math
import re
import secrets as _secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# MASTER PROMPT (returned by /api/nexus/prompt)
# ─────────────────────────────────────────────────────────────────────────────
MASTER_PROMPT_VERSION = "1.0"
MASTER_PROMPT = """NEXUS Autonomous Engineering System — Master Prompt v1.0
You are NEXUS, a self-directed, multi-layered reasoning and execution engine.
Operate across 4 simultaneous layers: STRATEGIC, TACTICAL, EXECUTION, SENTINEL.
Principles: Autonomy-first · Evidence-based completion · Zero-regression guarantee ·
Minimum footprint · Security by default · Self-aware state · Progressive context
compression · Measurable outcomes · Adversarial self-review · Long-horizon memory.
For every non-trivial task produce: STRATEGIC BRIEF -> TASK GRAPH -> EXECUTION ->
SENTINEL REVIEW -> EVIDENCE. Update PROJECT GENOME after each iteration.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Secret / risk detection (Sentinel)
# ─────────────────────────────────────────────────────────────────────────────
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("aws_access_key",      re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_key",      re.compile(r"(?i)aws(.{0,20})?(secret|sk)[\"'\s:=]+([A-Za-z0-9/+=]{40})")),
    ("github_token",        re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("openai_key",          re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("nvidia_key",          re.compile(r"nvapi-[A-Za-z0-9_-]{40,}")),
    ("slack_token",         re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("google_api_key",      re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("private_rsa_key",     re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----")),
    ("jwt",                 re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("generic_bearer",      re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("password_assignment", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*[\"'][^\"'\s]{6,}")),
]

OWASP_HEURISTICS: List[Tuple[str, str, re.Pattern]] = [
    ("A03_injection_sql",        "Potential SQL string concatenation",   re.compile(r"(?i)(SELECT|INSERT|UPDATE|DELETE)\b.*[\"'].*\+\s*\w+")),
    ("A03_injection_shell",      "Use of os.system / shell=True",        re.compile(r"(os\.system|subprocess\.[A-Za-z]+\([^)]*shell\s*=\s*True)")),
    ("A02_crypto_weak",          "Weak hash (MD5/SHA1)",                 re.compile(r"hashlib\.(md5|sha1)\b")),
    ("A05_misconfig_debug",      "Debug flag enabled",                   re.compile(r"(?i)\bdebug\s*=\s*True\b")),
    ("A07_auth_hardcoded",       "Hardcoded credentials",                re.compile(r"(?i)(api[_-]?key|secret)\s*=\s*[\"'][^\"']{8,}[\"']")),
    ("A09_logging_secrets",      "Logging a secret-like value",          re.compile(r"(?i)(log|print)\s*\(.*(password|secret|token).*\)")),
    ("A10_ssrf_open_redirect",   "Unvalidated request to dynamic URL",   re.compile(r"requests\.(get|post|put)\s*\(\s*[a-z_][a-z0-9_]*\s*\)")),
]

def _redact(s: str) -> str:
    if len(s) <= 8:
        return "*" * len(s)
    return s[:4] + "…" + s[-4:]

def sentinel_scan(text: str, *, language: str = "auto") -> Dict[str, Any]:
    """Static-analysis scan for secrets + OWASP heuristics. Returns findings list."""
    findings: List[Dict[str, Any]] = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            findings.append({
                "type": "secret",
                "rule": name,
                "severity": "high",
                "line": text.count("\n", 0, m.start()) + 1,
                "match_preview": _redact(m.group(0)),
            })
    for code, msg, pat in OWASP_HEURISTICS:
        for m in pat.finditer(text):
            findings.append({
                "type": "owasp",
                "rule": code,
                "message": msg,
                "severity": "medium" if code.startswith("A05") or code.startswith("A09") else "high",
                "line": text.count("\n", 0, m.start()) + 1,
                "snippet": text[max(0, m.start()-20):m.end()+20].strip()[:120],
            })
    score = 100 - min(100, sum(20 if f["severity"] == "high" else 10 for f in findings))
    return {
        "ok": len(findings) == 0,
        "score": score,
        "findings": findings,
        "stats": {
            "lines": text.count("\n") + 1,
            "chars": len(text),
            "high_count": sum(1 for f in findings if f["severity"] == "high"),
            "med_count": sum(1 for f in findings if f["severity"] == "medium"),
        },
        "language": language,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Strategic Brief generator (rule-based, deterministic — no LLM dep)
# ─────────────────────────────────────────────────────────────────────────────
RISK_KEYWORDS = {
    "migration":  ("Data loss during migration",  "Dual-write + reversible migration script + dry-run on snapshot"),
    "auth":       ("Lockout / token leakage",     "Rotate via secrets manager; verify all clients before old key revoked"),
    "deploy":     ("Production downtime",         "Canary 10% → 5min → 100%; auto-rollback on p99 + error-rate breach"),
    "payment":    ("Double-charge / chargeback",  "Idempotency keys + Stripe test mode E2E pass before live"),
    "delete":     ("Irreversible data loss",      "Soft-delete first, hard-delete after 7-day retention window"),
    "scale":      ("Resource exhaustion",         "Load test 3x expected; horizontal autoscale with circuit breaker"),
    "secret":     ("Credential exposure",         "Pre-commit secret scan + per-env vault; never in source"),
    "schema":     ("Backwards incompatibility",   "Expand-then-contract migration; deploy reader before writer"),
}

def strategic_brief(objective: str, *, constraints: Optional[List[str]] = None) -> Dict[str, Any]:
    """Deterministic Strategic Brief generator — Triforce reasoning skeleton."""
    obj = objective.strip()
    obj_low = obj.lower()
    detected_risks: List[Dict[str, str]] = []
    for kw, (risk, mit) in RISK_KEYWORDS.items():
        if kw in obj_low:
            detected_risks.append({"risk": risk, "mitigation": mit, "trigger": kw})
    if not detected_risks:
        detected_risks = [
            {"risk": "Scope creep mid-implementation",                "mitigation": "Lock acceptance criteria in this brief; defer extras to Backlog"},
            {"risk": "Hidden coupling discovered after partial build", "mitigation": "Map dependency graph in tactical phase before writing code"},
            {"risk": "Untested edge case fails in production",         "mitigation": "Auto-synthesise unit + property tests for new functions"},
        ]
    effort_min = max(15, len(obj.split()) * 4 + len(detected_risks) * 10)
    effort_h = round(effort_min / 60, 1)
    return {
        "objective": obj,
        "constraints": constraints or ["Backwards compatibility", "No new infra cost", "Production SLO unchanged"],
        "risks": detected_risks[:3],
        "architecture_decision": {
            "chosen": "Iterate within current stack (FastAPI + React + Mongo)",
            "rejected": [
                {"option": "Greenfield rewrite",    "reason": "Cost > value for current scope"},
                {"option": "Microservice split",    "reason": "Premature; no scaling pressure yet"},
            ],
        },
        "success_metrics": [
            "All new endpoints return 2xx under contract tests",
            "Sentinel scan score >= 90 on changed files",
            "Zero p99 latency regression > 5% on /api/* routes",
            "Test coverage delta >= 0 on touched modules",
        ],
        "estimated_effort": {"minutes": effort_min, "hours": effort_h, "token_budget": effort_min * 800},
        "triforce": {
            "first_principles": "What invariant must hold true regardless of implementation choice?",
            "analogy":          "Which canonical pattern (saga, CQRS, circuit breaker, ...) does this map to?",
            "inversion":        "What single change would make this catastrophically fail?",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Task Graph decomposition
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_PHASES = [
    ("design",   "Author ADR + draft schema",                   "strategic", []),
    ("scaffold", "Create stubs + types + tests skeleton",       "tactical",  ["design"]),
    ("build",    "Implement core logic",                        "execution", ["scaffold"]),
    ("verify",   "Unit + integration + sentinel scan",          "sentinel",  ["build"]),
    ("deploy",   "Canary rollout w/ auto-rollback guard",       "execution", ["verify"]),
    ("observe",  "Monitor metrics for 30min post-deploy",       "sentinel",  ["deploy"]),
]

def task_graph(objective: str, *, phases: Optional[List[str]] = None) -> Dict[str, Any]:
    nodes = []
    for nid, title, layer, deps in DEFAULT_PHASES:
        if phases and nid not in phases:
            continue
        nodes.append({
            "id": nid,
            "title": title,
            "layer": layer,
            "depends_on": deps,
            "status": "queued",
            "checkpoint": layer == "sentinel",
            "rollback_point": nid in ("build", "deploy"),
            "estimated_minutes": 20,
            "confidence": 85,
        })
    critical_path = [n["id"] for n in nodes]
    return {
        "objective": objective,
        "nodes": nodes,
        "critical_path": critical_path,
        "parallel_lanes": [],  # current scope is linear
        "total_estimated_minutes": sum(n["estimated_minutes"] for n in nodes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Cognitive load + entropy metrics on snippets
# ─────────────────────────────────────────────────────────────────────────────
def cognitive_load(code: str) -> Dict[str, Any]:
    lines = code.splitlines() or [""]
    nesting = max((len(l) - len(l.lstrip(" \t"))) // 2 for l in lines) if lines else 0
    cyclomatic = 1 + sum(code.count(k) for k in (" if ", " elif ", " for ", " while ", " and ", " or ", " except", " case "))
    unique_idents = len(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", code)))
    lloc = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
    score = round(min(100, (cyclomatic * 2.5) + (nesting * 4) + (lloc * 0.15)), 1)
    band = "low" if score < 25 else "medium" if score < 55 else "high" if score < 80 else "very_high"
    return {
        "lloc": lloc,
        "max_nesting": nesting,
        "cyclomatic_complexity": cyclomatic,
        "unique_identifiers": unique_idents,
        "cognitive_load_score": score,
        "band": band,
        "recommendation": {
            "low": "Healthy — ship it.",
            "medium": "Consider extracting one helper.",
            "high": "Refactor: split into >=2 functions, flatten nesting.",
            "very_high": "Block merge: cognitive load exceeds team threshold.",
        }[band],
    }

# ─────────────────────────────────────────────────────────────────────────────
# DB-backed registries (lazy bind)
# ─────────────────────────────────────────────────────────────────────────────
class NexusStore:
    def __init__(self, db):
        self.db = db
        self.briefs    = db.nexus_briefs
        self.plans     = db.nexus_plans
        self.decisions = db.nexus_decisions
        self.failures  = db.nexus_failures
        self.logs      = db.nexus_logs
        self.genome    = db.nexus_genome
        # Indexes (idempotent)
        try:
            self.decisions.create_index("number", unique=True)
            self.failures.create_index([("trigger", 1)])
            self.logs.create_index([("ts", -1)])
        except Exception:
            pass

    # ── Decision Records ────────────────────────────────────────────────────
    def next_decision_number(self) -> int:
        last = self.decisions.find_one(sort=[("number", -1)])
        return (last["number"] + 1) if last else 1

    def create_decision(self, *, title: str, context: str, options: List[str],
                        decision: str, consequences: str,
                        supersedes: Optional[int] = None) -> Dict[str, Any]:
        n = self.next_decision_number()
        doc = {
            "number": n,
            "id": f"DR-{n:03d}",
            "title": title.strip(),
            "context": context.strip(),
            "options": options,
            "decision": decision.strip(),
            "consequences": consequences.strip(),
            "supersedes": supersedes,
            "status": "accepted",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "review_after": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        self.decisions.insert_one(doc)
        doc.pop("_id", None)
        return doc

    def list_decisions(self) -> List[Dict[str, Any]]:
        return [{k: v for k, v in d.items() if k != "_id"}
                for d in self.decisions.find().sort("number", -1).limit(200)]

    # ── Failure Patterns ────────────────────────────────────────────────────
    def add_failure(self, *, trigger: str, failure: str, fix: str,
                    prevention: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        doc = {
            "id": _secrets.token_hex(8),
            "trigger": trigger,
            "failure": failure,
            "fix": fix,
            "prevention": prevention,
            "tags": tags or [],
            "occurrences": 1,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        existing = self.failures.find_one({"trigger": trigger, "failure": failure})
        if existing:
            self.failures.update_one(
                {"_id": existing["_id"]},
                {"$inc": {"occurrences": 1},
                 "$set": {"last_seen": doc["last_seen"], "fix": fix, "prevention": prevention}},
            )
            existing["occurrences"] += 1
            existing.pop("_id", None)
            return existing
        self.failures.insert_one(doc)
        doc.pop("_id", None)
        return doc

    def list_failures(self, *, q: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.failures.find({"$or": [
            {"trigger": {"$regex": q, "$options": "i"}},
            {"failure": {"$regex": q, "$options": "i"}},
        ]}) if q else self.failures.find()
        return [{k: v for k, v in d.items() if k != "_id"} for d in cur.sort("last_seen", -1).limit(200)]

    def match_failure(self, trigger_query: str) -> List[Dict[str, Any]]:
        q = trigger_query.lower()
        out = []
        for d in self.failures.find():
            if q in d.get("trigger", "").lower() or q in d.get("failure", "").lower():
                d.pop("_id", None)
                out.append(d)
        return out[:5]

    # ── Agent Log (Layer 3 audit trail) ─────────────────────────────────────
    def log(self, *, layer: str, node_id: str, status: str, action: str,
            reason: str = "", duration_ms: Optional[int] = None,
            result_preview: str = "", next_: str = "") -> Dict[str, Any]:
        doc = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "layer": layer,
            "node_id": node_id,
            "status": status,
            "duration_ms": duration_ms,
            "action": action,
            "reason": reason,
            "result_preview": result_preview[:500],
            "next": next_,
        }
        self.logs.insert_one(doc)
        doc.pop("_id", None)
        return doc

    def recent_logs(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        return [{k: v for k, v in d.items() if k != "_id"}
                for d in self.logs.find().sort("ts", -1).limit(limit)]

    # ── Project Genome (single doc; upsert) ─────────────────────────────────
    def get_genome(self) -> Dict[str, Any]:
        doc = self.genome.find_one({"_id": "genome"})
        if not doc:
            doc = {
                "_id": "genome",
                "project": "Devil Agent",
                "version": "3.0.0",
                "stack": ["FastAPI", "React+TS", "MongoDB", "Nginx", "Tailwind"],
                "adr_count": 0,
                "open_failures": 0,
                "last_deploy": None,
                "tech_debt": [],
                "baselines": {"p99_ms": 250, "coverage_pct": 0, "bundle_kb": 0},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.genome.insert_one(doc)
        # Refresh counters
        doc["adr_count"]      = self.decisions.count_documents({})
        doc["open_failures"]  = self.failures.count_documents({})
        doc["log_entries"]    = self.logs.count_documents({})
        self.genome.update_one({"_id": "genome"},
                               {"$set": {"adr_count": doc["adr_count"],
                                         "open_failures": doc["open_failures"],
                                         "updated_at": datetime.now(timezone.utc).isoformat()}})
        doc.pop("_id", None)
        return doc

    def update_genome(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        patch = {k: v for k, v in patch.items() if k not in ("_id",)}
        patch["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.genome.update_one({"_id": "genome"}, {"$set": patch}, upsert=True)
        return self.get_genome()


# Module-level store (set by server on startup)
_store: Optional[NexusStore] = None

def init(db) -> NexusStore:
    global _store
    _store = NexusStore(db)
    return _store

def store() -> NexusStore:
    if _store is None:
        raise RuntimeError("nexus_module not initialised — call init(db) on startup")
    return _store
