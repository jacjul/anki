from pydantic import BaseModel, ConfigDict, Field
from typing import Optional 
import enum

class CreateDeck(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    public: Optional[bool] = True 

class UpdateDeck(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=40)
    public: bool

class ActionDeck(enum.Enum):
    RENAME = "rename"
    PUBLIC = "public"


class DeckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    public: bool
    owner_id: int