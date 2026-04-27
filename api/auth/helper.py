from pwdlib import PasswordHash
from dotenv import load_dotenv
from jose import jwt 
import os 
from datetime import datetime, timedelta
import uuid
import hashlib


load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES= int (os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS= int (os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

ALGORITHM = os.getenv("ALGORITHM", "HS256")

passwordhash = PasswordHash.recommended()

def hash_password(plain_password:str):
    return passwordhash.hash(plain_password)

def verify_password (plain_password:str, hashed_password:str):
    return passwordhash.verify(plain_password, hashed_password)


def create_access_token(data:dict, expiry_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)-> str:
    to_encode = data.copy()
    exp = datetime.now() + timedelta(minutes = expiry_minutes)
    to_encode.update({"exp":exp})

    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return access_token

def create_refresh_token(data:dict, expiry_days=REFRESH_TOKEN_EXPIRE_DAYS)->tuple[str,uuid.UUID]:
    to_encode = data.copy()
    jti = uuid.uuid4()
    exp = datetime.now() + timedelta(days=expiry_days)
    to_encode.update({"exp":exp, "jti":jti})

    refresh_token=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token,jti

def hash_refresh_token(token:str):
    return hashlib.sha256(token.encode()).hexdigest()

def validate_refresh_token(plain,hashed):
    return hash_refresh_token(plain) == hashed

def decode_refresh_token(token:str)->dict:
    return jwt.decode(token, SECRET_KEY,algorithms =ALGORITHM)
