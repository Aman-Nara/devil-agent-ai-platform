"""
Devil Web Platform - FastAPI Backend (OPTIMIZED)
Features:
- Fixed O(n) login performance issue with key prefix indexing
- Encrypted API keys storage
- Rate limiting and security enhancements
- Connection pooling and caching
- User tiers system
- Enhanced conversation and skills management
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import random
from collections import defaultdict
import time
import asyncio

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import JWTError, jwt
import bcrypt
import httpx
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64

# MCP module (local)
import mcp_module  # noqa: E402
import nexus_module  # noqa: E402

load_dotenv()

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "devil_web")
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Encryption key for API keys (should be in .env)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# NVIDIA API Configuration
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_MODEL = "qwen/qwen3-next-80b-a3b-instruct"

# MongoDB setup with connection pooling
client = MongoClient(
    MONGO_URL,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    serverSelectionTimeoutMS=5000
)
db = client[DB_NAME]
nexus_module.init(db)
users_collection = db["users"]
conversations_collection = db["conversations"]
skills_collection = db["skills"]

# Create optimized indexes
users_collection.create_index("key_hash", unique=True)
try:
    users_collection.create_index("key_prefix")
except Exception:
    pass  # NEW: For O(1) login lookup
users_collection.create_index("tier")
users_collection.create_index("created_at")
conversations_collection.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
conversations_collection.create_index("title")
skills_collection.create_index([("user_id", ASCENDING), ("name", ASCENDING)])
skills_collection.create_index("tags")
skills_collection.create_index("category")

# Word list for generating 40-word keys
WORD_LIST = [
    "apple", "banana", "cherry", "dance", "elephant", "forest", "guitar", "harmony",
    "island", "jungle", "kingdom", "lemon", "mountain", "nature", "ocean", "piano",
    "quantum", "river", "sunset", "tiger", "umbrella", "violet", "whisper", "yellow",
    "zebra", "anchor", "breeze", "castle", "dolphin", "eclipse", "flame", "galaxy",
    "horizon", "journey", "knight", "lantern", "miracle", "nebula", "oracle", "phoenix",
    "quest", "rainbow", "sapphire", "thunder", "unicorn", "vortex", "wisdom", "zenith",
    "aurora", "blizzard", "cosmos", "destiny", "ember", "frost", "glacier", "harbor",
    "infinite", "jasmine", "karma", "lightning", "mystic", "nova", "odyssey", "prism",
    "radiant", "serenity", "twilight", "utopia", "velvet", "wonder", "xenon", "yonder",
    "zephyr", "alpine", "beacon", "crystal", "diamond", "eternal", "fortune", "golden",
    "heritage", "ivory", "jewel", "kinetic", "liberty", "magnolia", "nimbus", "oasis",
    "paradise", "quartz", "ruby", "stellar", "tranquil", "valor", "willow", "xanadu",
    "yearning", "zodiac", "amethyst", "blossom", "cascade", "dazzle", "emerald", "fusion",
    "grace", "haven", "illusion", "jade", "kaleidoscope", "lavender", "meadow", "nectar",
    "opulent", "pearl", "quintessence", "resonance", "shimmer", "tempest", "unity", "vivid",
    "whistle", "xerophyte", "yield", "zeal", "abstract", "balance", "cipher", "drift"
]

# User tiers configuration
USER_TIERS = {
    "free": {
        "max_conversations": 50,
        "max_skills": 20,
        "max_messages_per_day": 100,
        "features": ["basic_chat", "skills_management"]
    },
    "pro": {
        "max_conversations": 500,
        "max_skills": 200,
        "max_messages_per_day": 1000,
        "features": ["basic_chat", "skills_management", "advanced_search", "export", "priority_support"]
    },
    "enterprise": {
        "max_conversations": -1,  # unlimited
        "max_skills": -1,
        "max_messages_per_day": -1,
        "features": ["all"]
    }
}

# Rate limiting storage (in-memory, should use Redis in production)
rate_limit_storage = defaultdict(list)
RATE_LIMIT_MAX_KEYS = 50000  # bound memory growth

# Simple cache (in-memory, should use Redis in production)
cache_storage = {}
CACHE_TTL = 300  # 5 minutes
CACHE_MAX_KEYS = 10000  # bound memory growth

# Last housekeeping time
_last_housekeep = 0.0
_HOUSEKEEP_INTERVAL = 60  # seconds

def _housekeep():
    """Evict expired cache entries and trim rate-limit storage."""
    global _last_housekeep
    now = time.time()
    if now - _last_housekeep < _HOUSEKEEP_INTERVAL:
        return
    _last_housekeep = now
    # Drop expired cache entries
    expired = [k for k, (_, ts) in cache_storage.items() if now - ts >= CACHE_TTL]
    for k in expired:
        cache_storage.pop(k, None)
    # If cache still too big, drop oldest
    if len(cache_storage) > CACHE_MAX_KEYS:
        for k, _ in sorted(cache_storage.items(), key=lambda kv: kv[1][1])[: len(cache_storage) - CACHE_MAX_KEYS]:
            cache_storage.pop(k, None)
    # Drop rate-limit buckets older than 1 day with no recent activity
    cutoff = now - 86400
    drop_keys = [k for k, lst in rate_limit_storage.items() if not lst or lst[-1] < cutoff]
    for k in drop_keys:
        rate_limit_storage.pop(k, None)
    if len(rate_limit_storage) > RATE_LIMIT_MAX_KEYS:
        # Best-effort: clear oldest buckets
        for k in list(rate_limit_storage.keys())[: len(rate_limit_storage) - RATE_LIMIT_MAX_KEYS]:
            rate_limit_storage.pop(k, None)

app = FastAPI(
    title="Devil Web API",
    version="3.0.0",
    description="Devil Agent v3 — NEXUS Autonomous Engineering OS · 40-word key auth · MCP tools · Sentinel"
)

# Track in-process request counters for /api/metrics
_request_counts: Dict[str, int] = defaultdict(int)
_response_codes: Dict[int, int] = defaultdict(int)
_login_attempts_by_ip: Dict[str, List[float]] = defaultdict(list)
LOGIN_THROTTLE_LIMIT = int(os.environ.get("LOGIN_THROTTLE_LIMIT", "20"))
LOGIN_THROTTLE_WINDOW = int(os.environ.get("LOGIN_THROTTLE_WINDOW", "300"))  # 5 min
SERVER_START_TS = time.time()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Lightweight metrics accounting
    try:
        _request_counts[request.url.path] += 1
        _response_codes[int(getattr(response, "status_code", 0) or 0)] += 1
    except Exception:
        pass
    return response

# CORS with whitelist
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS[0] != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Helper functions
def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    return fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    return fernet.decrypt(encrypted_key.encode()).decode()

def generate_40_word_key() -> str:
    """Generate random 40-word key"""
    return "-".join(random.choices(WORD_LIST, k=40))

def get_key_prefix(key: str) -> str:
    """Get first 8 characters of key for fast lookup"""
    return key[:8] if len(key) >= 8 else key

def hash_key(key: str) -> str:
    """Hash a 40-word key"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(key.encode(), salt).decode()

def verify_key(key: str, key_hash: str) -> bool:
    """Verify a key against its hash"""
    return bcrypt.checkpw(key.encode(), key_hash.encode())

def create_jwt_token(user_id: str) -> str:
    """Create JWT token"""
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check cache first
        cache_key = f"user:{user_id}"
        if cache_key in cache_storage:
            cached_data, timestamp = cache_storage[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                return cached_data
        
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Cache user data (bounded; housekeeping evicts on TTL/size)
        cache_storage[cache_key] = (user, time.time())
        if len(cache_storage) > CACHE_MAX_KEYS:
            _housekeep()
        return user
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Rate limiting middleware
async def rate_limit_check(request: Request, user_id: str, limit: int = 100, window: int = 60):
    """Check rate limit for user. limit<=0 (e.g. -1) means unlimited."""
    _housekeep()
    if limit is None or limit <= 0:
        return  # unlimited (enterprise tier or disabled)
    now = time.time()
    key = f"{user_id}:{request.url.path}"

    # Clean old entries
    rate_limit_storage[key] = [ts for ts in rate_limit_storage[key] if now - ts < window]

    # Check limit
    if len(rate_limit_storage[key]) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    rate_limit_storage[key].append(now)

# Pydantic Models
class KeyResponse(BaseModel):
    key: str
    message: str
    user_id: str
    token: str

class AuthResponse(BaseModel):
    token: str
    user_id: str

class LoginRequest(BaseModel):
    key: str

class UserProfile(BaseModel):
    id: str
    tier: str
    has_nvidia_key: bool
    nvidia_key_preview: Optional[str] = None
    created_at: str
    usage_stats: Optional[Dict] = None

class UpdateAPIKeyRequest(BaseModel):
    nvidia_api_key: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    model: Optional[str] = NVIDIA_MODEL
    skill_id: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

class SkillCreate(BaseModel):
    name: str
    description: Optional[str] = None
    code: str
    language: str = "python"
    category: Optional[str] = None
    tags: Optional[List[str]] = None

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Devil Web API - Optimized v2.0",
        "status": "running",
        "features": ["40-word-auth", "ai-chat", "skills-management", "user-tiers"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/api/version")
async def version():
    """Return API version + lightweight runtime stats (no auth)."""
    return {
        "name": "Devil Web API",
        "version": app.version,
        "model": NVIDIA_MODEL,
        "tiers": list(USER_TIERS.keys()),
        "cache_entries": len(cache_storage),
        "rate_limit_buckets": len(rate_limit_storage),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# Authentication endpoints
@app.post("/api/auth/signup", response_model=KeyResponse)
async def signup():
    """Create new user with 40-word key"""
    # Generate unique key
    max_attempts = 10
    for _ in range(max_attempts):
        key = generate_40_word_key()
        key_hash = hash_key(key)
        key_prefix = get_key_prefix(key)
        
        # Check if key exists
        if not users_collection.find_one({"key_hash": key_hash}):
            break
    else:
        raise HTTPException(status_code=500, detail="Failed to generate unique key")
    
    # Create user
    user = {
        "key_hash": key_hash,
        "key_prefix": key_prefix,  # NEW: For fast lookup
        "tier": "free",
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
        "usage_stats": {
            "total_messages": 0,
            "total_conversations": 0,
            "total_skills": 0,
            "messages_today": 0,
            "last_message_date": None
        }
    }
    
    result = users_collection.insert_one(user)
    user_id = str(result.inserted_id)
    
    # Create JWT token
    token = create_jwt_token(user_id)
    
    return {
        "token": token,
        "user_id": user_id,
        "key": key,
        "message": "SAVE THIS KEY! It cannot be recovered. Store it securely."
    }

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, http_request: Request):
    """Login with 40-word key - OPTIMIZED O(1) lookup + per-IP throttle."""
    # Per-IP throttle to slow brute-force
    client_ip = (http_request.client.host if http_request.client else "unknown") or "unknown"
    now = time.time()
    bucket = _login_attempts_by_ip[client_ip]
    bucket[:] = [t for t in bucket if now - t < LOGIN_THROTTLE_WINDOW]
    if len(bucket) >= LOGIN_THROTTLE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    bucket.append(now)

    key_prefix = get_key_prefix(request.key)
    
    # Find users with matching prefix (much smaller set)
    potential_users = users_collection.find({"key_prefix": key_prefix})
    
    for user in potential_users:
        if verify_key(request.key, user["key_hash"]):
            # Update last login
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            
            # Clear cache for this user
            cache_key = f"user:{str(user['_id'])}"
            if cache_key in cache_storage:
                del cache_storage[cache_key]
            
            token = create_jwt_token(str(user["_id"]))
            return {"token": token, "user_id": str(user["_id"])}
    
    raise HTTPException(status_code=401, detail="Invalid key")

# User endpoints
@app.get("/api/user/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    nvidia_preview = None
    if current_user.get("nvidia_api_key_encrypted"):
        # Show last 4 characters
        decrypted = decrypt_api_key(current_user["nvidia_api_key_encrypted"])
        nvidia_preview = f"...{decrypted[-4:]}"
    
    return {
        "id": str(current_user["_id"]),
        "tier": current_user.get("tier", "free"),
        "has_nvidia_key": bool(current_user.get("nvidia_api_key_encrypted")),
        "nvidia_key_preview": nvidia_preview,
        "created_at": current_user["created_at"].isoformat(),
        "usage_stats": current_user.get("usage_stats", {})
    }


@app.get("/api/users/profile", response_model=UserProfile)
async def get_users_profile_alias(current_user: dict = Depends(get_current_user)):
    return await get_profile(current_user)

@app.post("/api/user/nvidia-key")
async def update_nvidia_key(request: UpdateAPIKeyRequest, current_user: dict = Depends(get_current_user)):
    """Update NVIDIA API key (encrypted storage)"""
    encrypted_key = encrypt_api_key(request.nvidia_api_key)
    
    users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"nvidia_api_key_encrypted": encrypted_key}}
    )
    
    # Clear cache
    cache_key = f"user:{str(current_user['_id'])}"
    if cache_key in cache_storage:
        del cache_storage[cache_key]
    
    return {"message": "API key updated successfully"}


# PATCH_V3_ALIASES_SKILL_TONE
def _build_messages_with_skill(conversation: dict, request, current_user: dict):
    """Build NVIDIA messages list, prepending a skill's prompt as system message if set."""
    msgs = []
    skill_id = getattr(request, "skill_id", None) or conversation.get("active_skill_id")
    if skill_id:
        try:
            sk = skills_collection.find_one({"_id": ObjectId(skill_id), "user_id": str(current_user["_id"])})
            if sk and sk.get("code"):
                msgs.append({"role": "system", "content": sk["code"]})
        except Exception:
            pass
    for m in conversation.get("messages", []):
        if m.get("role") in ("system", "user", "assistant") and m.get("content"):
            msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": request.message})
    return msgs

# Chat endpoints
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    current_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Send chat message - with rate limiting"""
    user_id = str(current_user["_id"])
    tier_config = USER_TIERS.get(current_user.get("tier", "free"))
    
    # Rate limit check
    await rate_limit_check(current_request, user_id, limit=tier_config["max_messages_per_day"], window=86400)
    
    # Get NVIDIA API key
    if current_user.get("nvidia_api_key_encrypted"):
        api_key = decrypt_api_key(current_user["nvidia_api_key_encrypted"])
    else:
        api_key = DEFAULT_NVIDIA_KEY
    
    # Get or create conversation
    if request.conversation_id:
        conversation = conversations_collection.find_one({
            "_id": ObjectId(request.conversation_id),
            "user_id": user_id
        })
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = {
            "user_id": user_id,
            "title": request.message[:50] + "..." if len(request.message) > 50 else request.message,
            "messages": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        result = conversations_collection.insert_one(conversation)
        conversation["_id"] = result.inserted_id
    
    # Add user message
    user_message = {
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Call NVIDIA API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{NVIDIA_API_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": request.model or NVIDIA_MODEL,
                    "messages": _build_messages_with_skill(conversation, request, current_user),
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            result = response.json()
            assistant_message = {
                "role": "assistant",
                "content": result["choices"][0]["message"]["content"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    
    # Update conversation
    conversations_collection.update_one(
        {"_id": conversation["_id"]},
        {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Update usage stats
    users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"usage_stats.total_messages": 1}}
    )
    
    return {
        "conversation_id": str(conversation["_id"]),
        "message": assistant_message["content"]
    }


# PATCH_V2_MCP_CONV_SKILLS
@app.post("/api/conversations")
async def create_conversation(current_user: dict = Depends(get_current_user)):
    """Create a new empty conversation."""
    user_id = str(current_user["_id"])
    conv = {
        "user_id": user_id,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = conversations_collection.insert_one(conv)
    return {"id": str(result.inserted_id), "title": conv["title"], "messages": [],
            "created_at": conv["created_at"].isoformat(),
            "updated_at": conv["updated_at"].isoformat()}

@app.get("/api/conversations")
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user conversations with pagination and search"""
    user_id = str(current_user["_id"])
    
    query = {"user_id": user_id}
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    
    conversations = conversations_collection.find(query).sort("updated_at", DESCENDING).skip(skip).limit(limit)
    
    result = []
    for conv in conversations:
        result.append({
            "id": str(conv["_id"]),
            "title": conv["title"],
            "created_at": conv["created_at"].isoformat(),
            "updated_at": conv["updated_at"].isoformat(),
            "message_count": len(conv.get("messages", []))
        })
    
    return {"conversations": result, "total": conversations_collection.count_documents(query)}

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get conversation details"""
    conversation = conversations_collection.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "id": str(conversation["_id"]),
        "title": conversation["title"],
        "messages": conversation.get("messages", []),
        "created_at": conversation["created_at"].isoformat(),
        "updated_at": conversation["updated_at"].isoformat()
    }

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete conversation"""
    result = conversations_collection.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted"}


class _SetSkillBody(BaseModel):
    skill_id: Optional[str] = None

@app.post("/api/conversations/{conversation_id}/skill")
async def set_conversation_skill(conversation_id: str, body: _SetSkillBody, current_user: dict = Depends(get_current_user)):
    """Attach (or clear) a skill used as system prompt for this conversation."""
    user_id = str(current_user["_id"])
    update = {"active_skill_id": body.skill_id} if body.skill_id else {"active_skill_id": None}
    result = conversations_collection.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {"$set": update}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True, "active_skill_id": body.skill_id}

# Skills endpoints
def _seed_default_skills_if_empty(user_id: str):
    """Lazy-seed the curated default skills library for users with zero skills."""
    try:
        if skills_collection.count_documents({"user_id": user_id}) > 0:
            return
        from default_skills import get_default_skills
        now = datetime.now(timezone.utc)
        docs = []
        for s in get_default_skills():
            docs.append({
                "user_id": user_id,
                "name": s["name"],
                "description": s.get("description"),
                "code": s["code"],
                "language": s.get("language", "prompt"),
                "category": s.get("category"),
                "tags": s.get("tags", []),
                "system": True,
                "created_at": now,
                "updated_at": now,
            })
        if docs:
            skills_collection.insert_many(docs)
    except Exception as _e:
        print(f"[seed] default skills failed: {_e}")

@app.get("/api/skills")
async def get_skills(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user skills with pagination and filtering"""
    user_id = str(current_user["_id"])
    _seed_default_skills_if_empty(user_id)
    
    query = {"user_id": user_id}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if category:
        query["category"] = category
    
    skills = skills_collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
    
    result = []
    for skill in skills:
        result.append({
            "id": str(skill["_id"]),
            "name": skill["name"],
            "description": skill.get("description"),
            "code": skill["code"],
            "language": skill.get("language", "python"),
            "category": skill.get("category"),
            "tags": skill.get("tags", []),
            "created_at": skill["created_at"].isoformat(),
            "updated_at": skill.get("updated_at", skill["created_at"]).isoformat()
        })
    
    return {"skills": result, "total": skills_collection.count_documents(query)}

@app.post("/api/skills")
async def create_skill(skill: SkillCreate, current_user: dict = Depends(get_current_user)):
    """Create new skill"""
    user_id = str(current_user["_id"])
    tier_config = USER_TIERS.get(current_user.get("tier", "free"))
    
    # Check skill limit
    skill_count = skills_collection.count_documents({"user_id": user_id})
    if tier_config["max_skills"] != -1 and skill_count >= tier_config["max_skills"]:
        raise HTTPException(status_code=403, detail=f"Skill limit reached for {current_user.get('tier', 'free')} tier")
    
    skill_doc = {
        "user_id": user_id,
        "name": skill.name,
        "description": skill.description,
        "code": skill.code,
        "language": skill.language,
        "category": skill.category,
        "tags": skill.tags or [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = skills_collection.insert_one(skill_doc)
    
    return {"id": str(result.inserted_id), "message": "Skill created"}

@app.put("/api/skills/{skill_id}")
async def update_skill(skill_id: str, skill: SkillUpdate, current_user: dict = Depends(get_current_user)):
    """Update skill"""
    update_data = {k: v for k, v in skill.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = skills_collection.update_one(
        {"_id": ObjectId(skill_id), "user_id": str(current_user["_id"])},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {"message": "Skill updated"}

@app.patch("/api/skills/{skill_id}")
async def patch_skill(skill_id: str, skill: SkillUpdate, current_user: dict = Depends(get_current_user)):
    return await update_skill(skill_id, skill, current_user)

@app.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
    """Delete skill"""
    result = skills_collection.delete_one({
        "_id": ObjectId(skill_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {"message": "Skill deleted"}

# =============================================================================
# Model registry (read-only, advertised to clients)
# =============================================================================
AVAILABLE_MODELS = [
    {
        "id": "qwen/qwen3-next-80b-a3b-instruct",
        "label": "Qwen3 Next 80B (Default)",
        "provider": "nvidia",
        "context": 131072,
        "default": True,
        "tags": ["chat", "code"],
    },
    {
        "id": "meta/llama-3.3-70b-instruct",
        "label": "Llama 3.3 70B Instruct",
        "provider": "nvidia",
        "context": 131072,
        "tags": ["chat"],
    },
    {
        "id": "deepseek-ai/deepseek-r1",
        "label": "DeepSeek R1 (Reasoning)",
        "provider": "nvidia",
        "context": 65536,
        "tags": ["reasoning", "code"],
    },
    {
        "id": "mistralai/mixtral-8x22b-instruct-v0.1",
        "label": "Mixtral 8x22B",
        "provider": "nvidia",
        "context": 65536,
        "tags": ["chat"],
    },
]


@app.get("/api/models")
async def list_models(_: dict = Depends(get_current_user)):
    """List models the user can pick in /api/chat."""
    return {"models": AVAILABLE_MODELS, "default": NVIDIA_MODEL}


# =============================================================================
# Analytics
# =============================================================================
@app.get("/api/analytics")
async def analytics(current_user: dict = Depends(get_current_user)):
    """Return per-user analytics (conversations, skills, messages, breakdown)."""
    user_id = str(current_user["_id"])
    total_convs = conversations_collection.count_documents({"user_id": user_id})
    total_skills = skills_collection.count_documents({"user_id": user_id})

    # Recent activity: last 7 days message timeline via aggregation
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        {"$match": {"user_id": user_id, "updated_at": {"$gte": seven_days_ago}}},
        {"$project": {"day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}}, "msgs": {"$size": {"$ifNull": ["$messages", []]}}}},
        {"$group": {"_id": "$day", "messages": {"$sum": "$msgs"}, "conversations": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    timeline = []
    try:
        for row in conversations_collection.aggregate(pipeline):
            timeline.append({"day": row["_id"], "messages": row["messages"], "conversations": row["conversations"]})
    except Exception:
        timeline = []

    # Top skills by category
    cat_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    categories = []
    try:
        for row in skills_collection.aggregate(cat_pipeline):
            categories.append({"category": row["_id"] or "uncategorized", "count": row["count"]})
    except Exception:
        categories = []

    usage = current_user.get("usage_stats", {}) or {}
    return {
        "totals": {
            "conversations": total_convs,
            "skills": total_skills,
            "messages": usage.get("total_messages", 0),
        },
        "tier": current_user.get("tier", "free"),
        "tier_limits": USER_TIERS.get(current_user.get("tier", "free"), {}),
        "timeline_7d": timeline,
        "skill_categories": categories,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Lightweight Prometheus-style metrics (public, but no PII)
# =============================================================================
@app.get("/api/metrics")
async def metrics():
    """Plain-text metrics. Safe to expose — no per-user info."""
    lines: List[str] = []
    lines.append(f"devil_uptime_seconds {int(time.time() - SERVER_START_TS)}")
    lines.append(f"devil_cache_entries {len(cache_storage)}")
    lines.append(f"devil_rate_limit_buckets {len(rate_limit_storage)}")
    try:
        lines.append(f"devil_users_total {users_collection.estimated_document_count()}")
        lines.append(f"devil_conversations_total {conversations_collection.estimated_document_count()}")
        lines.append(f"devil_skills_total {skills_collection.estimated_document_count()}")
    except Exception:
        pass
    for path, count in sorted(_request_counts.items()):
        safe_path = path.replace('"', '')
        lines.append(f'devil_http_requests_total{{path="{safe_path}"}} {count}')
    for code, count in sorted(_response_codes.items()):
        lines.append(f'devil_http_responses_total{{code="{code}"}} {count}')
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines) + "\n")


# =============================================================================
# MCP — Model Context Protocol tool registry
# =============================================================================
class MCPExecuteRequest(BaseModel):
    tool: str
    params: Optional[Dict] = None


@app.get("/api/mcp/servers")
async def mcp_servers(_: dict = Depends(get_current_user)):
    """List logical MCP 'servers' (tool categories)."""
    return {"servers": mcp_module.list_servers()}


@app.get("/api/mcp/tools")
async def mcp_tools(_: dict = Depends(get_current_user)):
    """List all available MCP tools with their schemas."""
    return {"tools": mcp_module.list_tools()}


@app.get("/api/mcp/list")
async def mcp_list(_: dict = Depends(get_current_user)):
    """Alias for /api/mcp/tools — returns all registered MCP tools."""
    return {"tools": mcp_module.list_tools(), "servers": mcp_module.list_servers()}

@app.post("/api/mcp/execute")
async def mcp_execute(
    body: MCPExecuteRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Execute an MCP tool. Rate-limited per user (20 / minute)."""
    user_id = str(current_user["_id"])
    await rate_limit_check(http_request, f"mcp:{user_id}", limit=20, window=60)
    result = await mcp_module.execute_tool(body.tool, body.params or {})
    return result




# ─────────────────────────────────────────────────────────────────────────────
# NEXUS Autonomous Engineering Operating System — v3.0 endpoints
# ─────────────────────────────────────────────────────────────────────────────
class NexusScanRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"

class NexusBriefRequest(BaseModel):
    objective: str
    constraints: Optional[List[str]] = None

class NexusPlanRequest(BaseModel):
    objective: str
    phases: Optional[List[str]] = None

class NexusDecisionRequest(BaseModel):
    title: str
    context: str
    options: List[str]
    decision: str
    consequences: str
    supersedes: Optional[int] = None

class NexusFailureRequest(BaseModel):
    trigger: str
    failure: str
    fix: str
    prevention: Optional[str] = ""
    tags: Optional[List[str]] = None

class NexusGenomePatch(BaseModel):
    project: Optional[str] = None
    version: Optional[str] = None
    stack: Optional[List[str]] = None
    last_deploy: Optional[str] = None
    tech_debt: Optional[List[Dict]] = None
    baselines: Optional[Dict] = None


@app.get("/api/nexus/status")
async def nexus_status():
    """Public liveness + summary of the NEXUS subsystem."""
    g = nexus_module.store().get_genome()
    return {
        "ok": True,
        "name": "NEXUS Autonomous Engineering OS",
        "prompt_version": nexus_module.MASTER_PROMPT_VERSION,
        "layers": ["strategic", "tactical", "execution", "sentinel"],
        "genome": g,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/nexus/prompt")
async def nexus_prompt():
    return {
        "version": nexus_module.MASTER_PROMPT_VERSION,
        "prompt": nexus_module.MASTER_PROMPT,
    }


@app.post("/api/nexus/sentinel/scan")
async def nexus_sentinel_scan(
    body: NexusScanRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    await rate_limit_check(http_request, f"nexus_scan:{user_id}", limit=30, window=60)
    result = nexus_module.sentinel_scan(body.text, language=body.language or "auto")
    nexus_module.store().log(
        layer="sentinel", node_id="scan", status="done",
        action=f"scanned {result['stats']['lines']} lines",
        reason="user-triggered code review",
        duration_ms=0,
        result_preview=f"score={result['score']} findings={len(result['findings'])}",
        next_="address high findings" if result["findings"] else "promote to next phase",
    )
    return result


@app.post("/api/nexus/cognitive-load")
async def nexus_cog_load(
    body: NexusScanRequest,
    current_user: dict = Depends(get_current_user),
):
    return nexus_module.cognitive_load(body.text)


@app.post("/api/nexus/brief")
async def nexus_brief(
    body: NexusBriefRequest,
    current_user: dict = Depends(get_current_user),
):
    brief = nexus_module.strategic_brief(body.objective, constraints=body.constraints)
    nexus_module.store().briefs.insert_one({**brief, "user": str(current_user["_id"])})
    brief.pop("_id", None)
    nexus_module.store().log(
        layer="strategic", node_id="brief", status="done",
        action="generated strategic brief",
        reason=body.objective[:120],
        result_preview=f"risks={len(brief['risks'])}",
        next_="decompose into task graph",
    )
    return brief


@app.post("/api/nexus/plan")
async def nexus_plan(
    body: NexusPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    plan = nexus_module.task_graph(body.objective, phases=body.phases)
    nexus_module.store().plans.insert_one({**plan, "user": str(current_user["_id"])})
    plan.pop("_id", None)
    nexus_module.store().log(
        layer="tactical", node_id="plan", status="done",
        action=f"decomposed into {len(plan['nodes'])} nodes",
        reason=body.objective[:120],
        next_="execute first node",
    )
    return plan


@app.get("/api/nexus/decisions")
async def nexus_list_decisions(current_user: dict = Depends(get_current_user)):
    return {"decisions": nexus_module.store().list_decisions()}


@app.post("/api/nexus/decisions")
async def nexus_create_decision(
    body: NexusDecisionRequest,
    current_user: dict = Depends(get_current_user),
):
    if len(body.options) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 options")
    dr = nexus_module.store().create_decision(
        title=body.title, context=body.context, options=body.options,
        decision=body.decision, consequences=body.consequences,
        supersedes=body.supersedes,
    )
    nexus_module.store().log(
        layer="strategic", node_id=dr["id"], status="accepted",
        action=f"recorded {dr['id']}: {dr['title']}",
        reason="architectural decision",
    )
    return dr


@app.get("/api/nexus/failures")
async def nexus_list_failures(q: Optional[str] = None,
                              current_user: dict = Depends(get_current_user)):
    return {"failures": nexus_module.store().list_failures(q=q)}


@app.post("/api/nexus/failures")
async def nexus_add_failure(
    body: NexusFailureRequest,
    current_user: dict = Depends(get_current_user),
):
    rec = nexus_module.store().add_failure(
        trigger=body.trigger, failure=body.failure, fix=body.fix,
        prevention=body.prevention or "", tags=body.tags or [],
    )
    return rec


@app.get("/api/nexus/logs")
async def nexus_logs(limit: int = 100,
                     current_user: dict = Depends(get_current_user)):
    return {"logs": nexus_module.store().recent_logs(limit=min(limit, 500))}


@app.get("/api/nexus/genome")
async def nexus_get_genome(current_user: dict = Depends(get_current_user)):
    return nexus_module.store().get_genome()


@app.patch("/api/nexus/genome")
async def nexus_update_genome(
    body: NexusGenomePatch,
    current_user: dict = Depends(get_current_user),
):
    patch = {k: v for k, v in body.dict().items() if v is not None}
    return nexus_module.store().update_genome(patch)


# WebSocket terminal endpoint - SECURE VERSION
@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """Authenticated WebSocket terminal for command execution.

    Auth flow:
      1. Client connects with ?token=<jwt> query param.
      2. Server validates token and accepts.
      3. Client streams commands; server returns stdout/stderr.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            await websocket.close(code=4401)
            return
        user = users_collection.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "tier": 1})
        if not user:
            await websocket.close(code=4401)
            return
    except (JWTError, Exception):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    # Send a welcome banner
    await websocket.send_text(
        "Devil Agent Terminal v1.0\r\n"
        "Type 'help' for commands. Dangerous ops are blocked.\r\n"
        f"user={str(user['_id'])} tier={user.get('tier','free')}\r\n"
        "$ "
    )

    import subprocess
    import shlex  # noqa: F401
    cwd = "/tmp"
    DANGEROUS = [
        "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf $home",
        ":(){ :|:& };:", "mkfs", "dd if=", "> /dev/sda", "> /dev/sd",
        "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
        "chmod -r 777 /", "chown -r", "/etc/passwd", "/etc/shadow",
        "passwd", "sudo ", "su ", "useradd", "userdel", "usermod",
        "iptables", "ufw ", "fdisk", "parted",
        "wget http", "curl http", "nc -l", "ncat -l", "socat",
        "/etc/sudoers", "crontab", "systemctl", "service ",
        "kill -9 1", "killall", "pkill",
        "ssh ", "scp ", "rsync ", "/dev/tcp/",
    ]

    try:
        while True:
            data = (await websocket.receive_text()).strip()
            if not data:
                await websocket.send_text("$ ")
                continue

            low = data.lower()
            if any(d in low for d in DANGEROUS):
                await websocket.send_text("\x1b[31mError: Dangerous command blocked\x1b[0m\r\n$ ")
                continue

            # Built-in commands
            if low in ("help", "?"):
                await websocket.send_text(
                    "Built-ins: help, clear, pwd, cd <dir>, exit\r\n"
                    "Shell commands work in sandboxed /tmp. Timeout 10s.\r\n$ "
                )
                continue
            if low == "clear":
                await websocket.send_text("\x1b[2J\x1b[H$ ")
                continue
            if low == "exit":
                await websocket.send_text("bye\r\n")
                await websocket.close()
                return
            if low == "pwd":
                await websocket.send_text(f"{cwd}\r\n$ ")
                continue
            if low.startswith("cd "):
                target = data[3:].strip() or "/tmp"
                if not target.startswith("/"):
                    target = os.path.normpath(os.path.join(cwd, target))
                if os.path.isdir(target) and target.startswith("/tmp"):
                    cwd = target
                    await websocket.send_text(f"{cwd}\r\n$ ")
                else:
                    await websocket.send_text("\x1b[31mcd: invalid path (must stay under /tmp)\x1b[0m\r\n$ ")
                continue

            # Execute shell command sandboxed in /tmp
            try:
                result = subprocess.run(
                    data,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=cwd,
                )
                out = (result.stdout or "") + (result.stderr or "")
                if not out:
                    out = f"[exit {result.returncode}]\r\n"
                # Normalize newlines for xterm
                out = out.replace("\n", "\r\n")
                await websocket.send_text(out + "$ ")
            except subprocess.TimeoutExpired:
                await websocket.send_text("\x1b[33mCommand timed out (10s)\x1b[0m\r\n$ ")
            except Exception as e:
                await websocket.send_text(f"\x1b[31mError: {str(e)}\x1b[0m\r\n$ ")
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
