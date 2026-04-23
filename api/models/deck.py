from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy import String
from typing import TYPE_CHECKING

from api.db.database import Base

if TYPE_CHECKING:
    from api.models.card import Card

class Deck(Base):
    __tablename__ ="deck"

    id:Mapped[int] = mapped_column(primary_key = True)
    name:Mapped[str] = mapped_column(String(40))
    public:Mapped[bool] 
    cards:Mapped[list["Card"]] = relationship(back_populates="deck", cascade="all, delete-orphan")