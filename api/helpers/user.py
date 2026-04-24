from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm 
from dotenv import load_dotenv
import os 
from datetime import datetime ,timedelta
from jose import jwt, JWTError

load_dotenv()

expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

password_hash = PasswordHash.recommended()


def hash_password(plain_password:str):

    hashed_password = password_hash.hash(plain_password)
    return hashed_password

def verify_password(plain_password:str, hashed_password:str):

    ver:bool = password_hash.verify(plain_password, hashed_password)
    return ver 

def create_access_token(data:dict , expire_minutes=expire_minutes) -> str:
    to_encode = data.copy()
    exp = datetime.now() +timedelta(minutes = expire_minutes)

    to_encode.update({"exp": exp})

    access_token = jwt.encode(to_encode,SECRET_KEY, algorithm = [ALGORITHM])

    return access_token

def decode_access_token(access_token:str)-> dict:
    return jwt.decode(access_token, SECRET_KEY, algorithm = [ALGORITHM])