import hashlib, hmac, re, secrets, time
from fastapi import Header, HTTPException
from app.db import pool
import redis
from app.config import settings

_redis = redis.Redis.from_url(settings.redis_url)

def new_secret() -> str:
    return secrets.token_urlsafe(32)

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def sign(secret: str, timestamp: str, body: bytes) -> str:
    message = timestamp.encode() + b'.' + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

def verify(secret: str, timestamp: str, body: bytes, signature: str, max_age: int = 300) -> bool:
    if abs(time.time() - int(timestamp)) > max_age:
        return False  # too old: blocks replay attacks
    return hmac.compare_digest(sign(secret, timestamp, body), signature)

INJECTION = re.compile(
    r'ignore (all )?(previous|prior) instructions|system prompt|reveal .*(key|secret|password)',
    re.IGNORECASE,
)

def looks_malicious(text: str) -> bool:
    return bool(INJECTION.search(text))

def current_agent(x_api_key: str = Header(...)):
    with pool.connection() as conn:
        row = conn.execute(
            'SELECT id FROM agents WHERE api_key_hash = %s AND is_active',
            (hash_key(x_api_key),),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail='Invalid API key')
    return row[0]

def rate_limit(agent_id, action: str, limit: int, window: int = 60):
    key = f'rl:{action}:{agent_id}'
    count = _redis.incr(key)
    if count == 1:
        _redis.expire(key, window)
    if count > limit:
        raise HTTPException(status_code=429, detail=f'Rate limit exceeded for {action}')
