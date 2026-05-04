from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy import String,ForeignKey
from typing import TYPE_CHECKING

from api.db.database import Base
from api.models.userdeck import UserDecks
if TYPE_CHECKING:
    from api.models.card import Card
    from api.models.user import User


class Deck(Base):
    __tablename__ ="deck"

    id:Mapped[int] = mapped_column(primary_key = True)
    name:Mapped[str] = mapped_column(String(40))
    public:Mapped[bool] = mapped_column(default = True )
    cards:Mapped[list["Card"]] = relationship(back_populates="deck", cascade="all, delete-orphan")  
    deck_memberships:Mapped[list[UserDecks]] = relationship(back_populates="deck")

    owner_id:Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    owner:Mapped["User"] = relationship("User", back_populates="decks_owned")
