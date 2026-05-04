from fastapi import APIRouter,Depends , HTTPException,Response, Cookie,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated,Optional
from sqlalchemy import select , or_ ,and_,update
from sqlalchemy.exc import SQLAlchemyError
import uuid

from api.schemas.user import UserRegister, UserProfile
from api.db.database import get_db 
from api.models.user import User
from api.models.token import Token
from api.core.settings import settings
from api.auth.helper import (
    hash_password,
    verify_password,
    create_access_token,
    get_client_ip,
    decode_token_or_401,
    create_refresh_token,
    hash_refresh_token,
    validate_refresh_token,
    create_csrf_token,
    validate_csrf,
    validate_origin,
    enforce_login_rate_limit,
    utc_now_naive,
)

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
        db.rollback()
        raise HTTPException(status_code = 500, detail="DB-Error")
    
@auth_router.post("/login")
def login(response:Response,request:Request, form_data:Annotated[OAuth2PasswordRequestForm,Depends()], db:Annotated[Session, Depends(get_db)]):

    enforce_login_rate_limit(request, form_data.username)

    user_exist = db.execute(select(User).where(User.username== form_data.username)).scalar_one_or_none()

    if not user_exist or not verify_password(form_data.password, user_exist.hashed_password):
        raise HTTPException(status_code = 401, detail="User not found or password incorrect.")
    
    family_id = uuid.uuid4()

    access_token = create_access_token({"sub": str(user_exist.id), "family_id": str(family_id)})

    refresh_token,jti,exp= create_refresh_token({"sub": str(user_exist.id), "family_id": str(family_id)})

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=refresh_token,
        secure=settings.secure_cookie,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.samesite_cookie,
        max_age=settings.COOKIE_MAX_AGE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )

    csrf_token = create_csrf_token()
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        secure=settings.secure_cookie,
        httponly=False,
        samesite=settings.samesite_cookie,
        max_age=settings.COOKIE_MAX_AGE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )



    new_token = Token(refresh_token_hash=hash_refresh_token(refresh_token), 
                      jti=jti,revoked=False, family_id=family_id,
                    expires_at=exp, user_id=user_exist.id, ip_address=get_client_ip(request))
    
    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    return {"access_token": access_token, "token_type":"bearer"}

@auth_router.post("/refresh")
def refresh_token(response:Response, request:Request, db:Annotated[Session, Depends(get_db)], refresh_token:Annotated[Optional[str], Cookie(alias=settings.COOKIE_NAME)] = None):

    validate_origin(request)
    validate_csrf(request)

    if not refresh_token: 
        raise HTTPException(status_code=401 ,detail="Refresh Cookie didnt exist")
    
    
    token_data = decode_token_or_401(refresh_token, "refresh")

    try:
        jti_old = uuid.UUID(token_data["jti"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        user_id = int(token_data["sub"])
    except (TypeError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    token_exist = db.execute(select(Token).where(and_(Token.jti == jti_old, Token.revoked==False))).scalar_one_or_none()

    if not token_exist:
        raise HTTPException(status_code=401 , detail="Invalid refresh token")
    
    if not validate_refresh_token(refresh_token,token_exist.refresh_token_hash):
        db.execute(
            update(Token)
            .where(Token.family_id == token_exist.family_id)
            .values(revoked=True, revoked_at=utc_now_naive())
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token({"sub": str(user_id), "family_id": str(token_exist.family_id)})

    new_refresh_token,jti,exp = create_refresh_token({"sub": str(user_id), "family_id": str(token_exist.family_id)})

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=new_refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.secure_cookie,
        samesite=settings.samesite_cookie,
        max_age=settings.COOKIE_MAX_AGE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )

    csrf_token = create_csrf_token()
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        secure=settings.secure_cookie,
        httponly=False,
        samesite=settings.samesite_cookie,
        max_age=settings.COOKIE_MAX_AGE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )

    new_token = Token(
        refresh_token_hash=hash_refresh_token(new_refresh_token),
        jti=jti,
        revoked=False,
        family_id=token_exist.family_id,
        expires_at=exp,
        user_id=user_id,
        ip_address=get_client_ip(request),
    )

    #invalidate old token
    db.execute(update(Token).where(Token.jti == jti_old).values(revoked=True, replaced_by_jti=jti ,revoked_at=utc_now_naive()))
    # add new token
    db.add(new_token)
    db.commit()
    db.refresh(new_token)



    return {"access_token": access_token, "token_type":"bearer"}

@auth_router.post("/logout")
def logout(response:Response, request:Request, db:Annotated[Session,Depends(get_db)], refresh_token:Annotated[Optional[str], Cookie(alias=settings.COOKIE_NAME)] = None):

    validate_origin(request)
    validate_csrf(request)

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")
    token_decoded = decode_token_or_401(refresh_token, "refresh")

    if not token_decoded["jti"]:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        family_id = uuid.UUID(token_decoded["family_id"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    #Revoke all tokens from user 
    db.execute(update(Token).where(Token.family_id==family_id).values(revoked=True, revoked_at=utc_now_naive()))
    db.commit()

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
        path=settings.COOKIE_PATH,
    )

    return {"message":"Logout successfully"}
def get_current_user(access_token:Annotated[str, Depends(oauth2scheme)], db:Annotated[Session,Depends(get_db)]):
    
    token_decode = decode_token_or_401(access_token, "access")

    try:
        user_id = int(token_decode["sub"])
    except (TypeError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid access token")


    family_id_raw = token_decode.get("family_id")

    try:
        family_id = uuid.UUID(str(family_id_raw))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid access token")

    active_family_token = db.execute(
        select(Token).where(
            and_(
                Token.user_id == user_id,
                Token.family_id == family_id,
                Token.revoked == False,
                Token.expires_at > utc_now_naive(),
            )
        )
    ).scalar_one_or_none()

    if active_family_token is None:
        raise HTTPException(status_code=401, detail="Session revoked")
    
    current_user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return current_user 

@auth_router.get("/me", response_model=UserProfile)
def get_my_profile(user: Annotated[User, Depends(get_current_user)]):
    return user 

    
    #Continue at number5 

