from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class CreateCard(BaseModel):
    frontside: str = Field(min_length=1, max_length=70)
    frontside_explain: Optional[str | None] = Field(default=None, max_length=2000)
    backside: str = Field(min_length=1, max_length=70)
    backside_explain: Optional[str | None] = Field(default=None, max_length=2000)
    deck_id: int = Field(gt=0)
    audio_front: Optional[str | None] = Field(default=None, max_length=500)
    audio_back: Optional[str | None] = Field(default=None, max_length=500)


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    frontside: str
    frontside_explain: Optional[str | None]
    backside: str
    backside_explain: Optional[str | None]
    audio_front: Optional[str | None]
    audio_back: Optional[str | None]
    deck_id: int




