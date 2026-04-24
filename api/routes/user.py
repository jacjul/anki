from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from fastapi import APIRouter,Depends,HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select 
from jose import JWTError

from api.schemas.user import UserRegister
from api.db.database import get_db
from api.models.user import User
from api.helpers.user import hash_password,create_access_token,verify_password,decode_access_token
user_router = APIRouter(prefix="/user")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/token")
#/register -> creates user in db

@user_router.post("/register")
def register_user(user:UserRegister, db:Session = Depends(get_db)):

    existent_email = db.execute(select(User).where(User.email ==user.email)).scalar_one_or_none()

    if existent_email:
        raise HTTPException(status_code=409, detail ="User with that emaill already exists")
    
    existent_username = db.execute(select(User).where(User.username ==user.username)).scalar_one_or_none()

    if existent_username:
        raise HTTPException(status_code=409, detail="Username already exists")

    hashed_password = hash_password(user.password)
    user_new = User(name = user.name, lastname = user.lastname,username= user.username ,email = user.email, hashed_password=hashed_password )

    try:
        db.add(user_new)
        db.commit()
        db.refresh(user_new)
        return {"message":"User created successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail ="Integrity Error")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="db Error")

#/token -> generates access token 
@user_router.post("/token")
def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()], db:Session =Depends(get_db)):
    user = db.execute(select(User).where(User.username == form_data.username)).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail = "User not found", headers={"WWW-Authenticate":"Bearer"})
    
    access_token = create_access_token({"sub":form_data.username})
    return {"access_token": access_token , "token_type":"bearer"}
#get_current_user -> decode access token 

def get_current_user(token:Annotated[str,Depends(oauth2_scheme)], db:Annotated[Session,Depends(get_db)]):
    
    credential_error = HTTPException(status_code = 401, detail="Couldnt validate credentials")
    
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")

        if not username:
            raise credential_error
    except JWTError:
        raise credential_error
    
    user = db.execute(select(User).where(User.username==username)).scalar_one_or_none()

    if not user:
        raise credential_error
    
    return user 
    