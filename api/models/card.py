from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy import String,LargeBinary,ForeignKey
from typing import TYPE_CHECKING

from api.db.database import Base

if TYPE_CHECKING:
    from api.models.deck import Deck

class Card(Base):
    __tablename__ = "card"

    id:Mapped[int] = mapped_column(primary_key = True)
    frontside:Mapped[str] = mapped_column(String(70))
    frontside_explain: Mapped[str] = mapped_column(nullable=True)
    backside:Mapped[str] = mapped_column(String(70))
    backside_explain: Mapped[str] = mapped_column(nullable=True)
    audio_front:Mapped[str|None] = mapped_column(String(500), nullable=True)
    audio_back:Mapped[str|None] = mapped_column(String(500), nullable=True)

    deck_id:Mapped[int] = mapped_column(ForeignKey("deck.id"))
    deck:Mapped["Deck"] = relationship(back_populates="cards")

