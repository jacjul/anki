from pydantic import BaseModel
from typing import Optional 
import enum

class CreateDeck(BaseModel):
    name:str
    public:Optional[bool] = True 

class UpdateDeck(BaseModel):
    id : int
    name:str
    public: bool

class ActionDeck(enum.Enum):
    RENAME = "rename"
    PUBLIC = "public"