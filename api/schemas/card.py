from pydantic import BaseModel 
from typing import Optional

class CreateCard(BaseModel):
        
    frontside : str
    frontside_explain : Optional[str|None] = None
    backside : str
    backside_explain : Optional[str|None] = None
    deck_id: int 
    audio_front: Optional[str|None] = None
    audio_back: Optional [str| None] = None




