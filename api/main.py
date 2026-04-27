from fastapi import FastAPI,Request, HTTPException 
from fastapi.responses import JSONResponse
from time import time
from fastapi.middleware.cors import CORSMiddleware 

from api.db.database import Base, engine
from api.routes.card import card_router
from api.routes.deck import deck_router
from api.auth.user import auth_router
from api.logger import logger 
app = FastAPI()


## run only once when run directly
if __name__ == "__main__":
    Base.metadata.create_all(bind =engine)

## adding the routes 
app.include_router(card_router,prefix="/api", tags=["card"])
app.include_router(deck_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

##adding the CORS-MW
origins = ["http://localhost:5173"]

app.add_middleware(CORSMiddleware, allow_origins=origins, 
                   allow_credentials = True , allow_methods=["*"], allow_headers=["*"])

### Logging 
@app.middleware("http")
async def create_logging(request, call_next):
    
    start_time = time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        duration = (time()-start_time ) *1000
        logger.info(f"{request.url.path} - {request.method} - {status_code} - Time: {duration}")


    return response 

@app.exception_handler(Exception)
async def log_unexpected_errors(request:Request, exc:Exception):
    logger.exception(f"unhandled error: {request.url.path} - {request.method}")
    return JSONResponse(status_code=500, content= {"detail":"Internal error"})

@app.exception_handler(HTTPException)
async def log_http_exception(request:Request, exc:HTTPException):
    logger.warning(f"HTTPException: {request.url.path} - {request.method} -{exc.status_code} - {exc.detail}")
    return JSONResponse( status_code =exc.status_code, content={"detail":exc.detail}, headers=exc.headers)