from fastapi import APIRouter,Depends , HTTPException,Response, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated,Optional
from sqlalchemy import select , or_ ,and_,update
from sqlalchemy.exc import SQLAlchemyError

from api.schemas.user import UserRegister
from api.db.database import get_db 
from api.models.user import User
from api.models.token import Token
from api.auth.helper import hash_password, verify_password, create_access_token, create_refresh_token,hash_refresh_token,validate_refresh_token,decode_refresh_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])

oauth2scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@auth_router.post("/register")
def register_user(form_data:UserRegister, db:Annotated[Session, Depends(get_db)]):

    existing_user = db.execute(select(User).where(or_(User.username==form_data.username, User.email==form_data.email))).scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code= 409, detail ="User with that username or email already exists")
    
    hashed_password = hash_password(form_data.password)

    user_data = form_data.model_dump(exclude={"password"})
    new_user = User(**user_data,hashed_password = hashed_password)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message":"success"}
    except SQLAlchemyError:
        raise HTTPException(status_code = 500, detail="DB-Error")
    
@auth_router.post("/login")
def login(response:Response, form_data:Annotated[OAuth2PasswordRequestForm,Depends()], db:Annotated[Session, Depends(get_db)]):

    user_exist = db.execute(select(User).where(User.username== form_data.username)).scalar_one_or_none()

    if not user_exist or not verify_password(form_data.password, user_exist.hashed_password):
        raise HTTPException(status_code = 401, detail="User not found or password incorrect.")
    
    access_token = create_access_token({"sub":form_data.username})

    refresh_token,jti = create_refresh_token({"sub":form_data.username})

    response.set_cookie(key="refresh_token", value=refresh_token, secure=True , httponly=True, samesite="strict", max_age=60*60*24*31) #slightly longer internal time of 30days

    new_token = Token(refresh_token_hash=hash_refresh_token(refresh_token), 
                      jti=jti,revoked=False )
    
    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    return {"access_token": access_token, "type":"bearer"}

@auth_router.post("/refresh")
def refresh_token(response:Response, refresh_token:Annotated[Optional[str],Cookie(None)], db:Annotated[Session, Depends(get_db)]):


    if not refresh_token: 
        raise HTTPException(status_code=404 ,detail="Refresh Cookie didnt exist")
    
    token_data = decode_refresh_token(refresh_token)
    jti_old = token_data["jti"]
    user_id = token_data["sub"]
    token_exist = db.execute(select(Token).where(and_(Token.jti == jti_old, Token.revoked==False))).scalar_one_or_none()

    if not token_exist:
        raise HTTPException(status_code=404 , detail="Couldnt find the token")
    
    access_token = create_access_token({"sub":token_data["sub"]})

    new_refresh_token,jti = create_refresh_token({"sub":user_id})

    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True,samesite="strict", max_age=60*60*24*31 )
    new_token = Token(refresh_token_hash=hash_refresh_token(new_refresh_token), jti=jti,revoked=False)

    #invalidate old token
    db.execute(update(Token).where(Token.jti == jti_old).values(revoked=True))

    # add new token
    db.add(new_token)
    db.commit()
    db.refresh(new_token)



    return {"access_token": access_token, "token_type":"bearer"}
    

    

