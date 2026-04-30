from pwdlib import PasswordHash
from jose import jwt,ExpiredSignatureError,JWTError
from fastapi import HTTPException,Request
from datetime import datetime, timedelta
import uuid
import hashlib
import ipaddress

from api.core.settings import settings

SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
ALGORITHM = settings.ALGORITHM
TRUSTED_PROXY_IPS = set(settings.TRUSTED_PROXY_IPS)

passwordhash = PasswordHash.recommended()

def hash_password(plain_password:str):
    return passwordhash.hash(plain_password)

def verify_password (plain_password:str, hashed_password:str):
    return passwordhash.verify(plain_password, hashed_password)


def create_access_token(data:dict, expiry_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)-> str:
    to_encode = data.copy()
    to_encode.setdefault("typ", "access")
    exp = datetime.now() + timedelta(minutes = expiry_minutes)
    to_encode.update({"exp":exp})

    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return access_token

def create_refresh_token(data:dict, expiry_days=REFRESH_TOKEN_EXPIRE_DAYS)->tuple[str,uuid.UUID,datetime]:
    to_encode = data.copy()
    jti = uuid.uuid4()
    to_encode.setdefault("typ", "refresh")
    exp = datetime.now() + timedelta(days=expiry_days)
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


