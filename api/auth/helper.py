from pwdlib import PasswordHash
from jose import jwt,ExpiredSignatureError,JWTError
from fastapi import HTTPException,Request
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from threading import Lock
from typing import Any, cast
import uuid
import hashlib
import ipaddress
import hmac
import secrets
import time
from redis.exceptions import RedisError
from api.core.redis_rate_limit import redis_client

from api.core.settings import settings

SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
ALGORITHM = settings.ALGORITHM
TRUSTED_PROXY_IPS = set(settings.TRUSTED_PROXY_IPS)
_LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_LOGIN_ATTEMPTS_LOCK = Lock()

RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local count = redis.call("INCR", key)
if count == 1 then
    redis.call("EXPIRE", key, window)
end
return count
"""

passwordhash = PasswordHash.recommended()

def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def hash_password(plain_password:str):
    return passwordhash.hash(plain_password)

def verify_password (plain_password:str, hashed_password:str):
    return passwordhash.verify(plain_password, hashed_password)


def create_access_token(data:dict, expiry_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)-> str:
    to_encode = data.copy()
    to_encode.setdefault("typ", "access")
    exp = utc_now_naive() + timedelta(minutes = expiry_minutes)
    to_encode.update({"exp":exp})

    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return access_token

def create_refresh_token(data:dict, expiry_days=REFRESH_TOKEN_EXPIRE_DAYS)->tuple[str,uuid.UUID,datetime]:
    to_encode = data.copy()
    jti = uuid.uuid4()
    to_encode.setdefault("typ", "refresh")
    exp = utc_now_naive() + timedelta(days=expiry_days)
    to_encode.update({"exp": exp, "jti": str(jti)})

    refresh_token=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token,jti,exp

def hash_refresh_token(token:str):
    return hashlib.sha256(token.encode()).hexdigest()

def validate_refresh_token(plain,hashed):
    return hash_refresh_token(plain) == hashed

def decode_token(token:str)->dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def decode_token_or_401(token:str, expected_type:str|None = None)->dict:
    try:
        decoded_token = decode_token(token)
        token_type = decoded_token.get("typ")
        if expected_type and token_type != expected_type:
            raise HTTPException(status_code=403, detail="Wrong Token Type")
        return decoded_token
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def _is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def get_client_ip(request:Request) -> str|None:
    client_host = request.client.host if request.client else None
    if not client_host:
        return None

    # Only trust forwarding headers if the immediate peer is a known proxy.
    if client_host not in TRUSTED_PROXY_IPS:
        return client_host if _is_valid_ip(client_host) else None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if _is_valid_ip(first_ip):
            return first_ip

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        real_ip = real_ip.strip()
        if _is_valid_ip(real_ip):
            return real_ip

    return client_host if _is_valid_ip(client_host) else None


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request) -> None:
    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)

    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=403, detail="Missing CSRF token")

    if not hmac.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        raise HTTPException(status_code=403, detail="Missing Origin header")
    if origin not in settings.CORS_ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin not allowed")


def _login_rate_limit_key(request: Request, username: str) -> str:
    client_ip = get_client_ip(request) or "unknown"
    normalized_username = username.strip().lower()
    return f"{settings.RATE_LIMIT_PREFIX}:rl:login:{client_ip}:{normalized_username}"


def _enforce_memory_login_rate_limit(rate_key: str) -> None:
    now = time.time()
    window_seconds = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_ATTEMPTS

    with _LOGIN_ATTEMPTS_LOCK:
        attempts = _LOGIN_ATTEMPTS[rate_key]
        while attempts and (now - attempts[0]) > window_seconds:
            attempts.popleft()

        attempts.append(now)
        if len(attempts) > max_attempts:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later")


def enforce_login_rate_limit(request: Request, username: str) -> None:
    rate_key = _login_rate_limit_key(request, username)
    window_seconds = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.LOGIN_RATE_LIMIT_ATTEMPTS

    try:
        eval_result = redis_client.eval(RATE_LIMIT_SCRIPT, 1, rate_key, window_seconds)
        current_count = int(cast(Any, eval_result))
        if current_count > max_attempts:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later")
        return
    except RedisError:
        # In local/dev environments, keep auth functional with in-memory fallback.
        if settings.ENV == "prod":
            raise HTTPException(status_code=503, detail="Login temporarily unavailable")

    _enforce_memory_login_rate_limit(rate_key)


def clear_rate_limit_state_for_tests() -> None:
    with _LOGIN_ATTEMPTS_LOCK:
        _LOGIN_ATTEMPTS.clear()

    pattern = f"{settings.RATE_LIMIT_PREFIX}:rl:login:*"
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
    except RedisError:
        # Tests should still be runnable without a local Redis instance.
        pass


