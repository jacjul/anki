from fastapi import FastAPI
from time import time
from fastapi.middleware.cors import CORSMiddleware 

from api.db.database import Base, engine
from api.routes.card import card_router
from api.logger import logger 
app = FastAPI()


## run only once when run directly
if __name__ == "__main__":
    Base.metadata.create_all(bind =engine)

## adding the routes 
app.include_router(card_router,prefix="/api", tags=["card"])

##adding the CORS-MW
origins = ["http://localhost:5173"]

app.add_middleware(CORSMiddleware, allow_origins=origins, 
                   allow_credentials = True , allow_methods=["*"], allow_headers=["*"])

### Logging 
@app.middleware("http")
async def create_logging(request, call_next):
    
    start_time = time()

    response = await call_next(request)

    duration = (time()-start_time ) *1000

    logger.info(f"{request.url.path} - {response.status_code} - Time: {duration}")

    return response 

