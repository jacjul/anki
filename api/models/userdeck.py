from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import Enum as SAEnum, UniqueConstraint,ForeignKey
from datetime import datetime, timezone
from enum import Enum 
from typing import TYPE_CHECKING

from api.db.database import Base
if TYPE_CHECKING:
    from api.models.user import User
    from api.models.deck import Deck
class EditorType(str,Enum):
    owner= "owner"
    editor= "editor"
    viewer="viewer"

class UserDecks(Base):
    __tablename__ ="user_decks"
    __table_args__ = (UniqueConstraint("user_id", "deck_id", name="uq_deck_user"),)
    
    id:Mapped[int] = mapped_column(primary_key=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    deck_id:Mapped[int] = mapped_column(ForeignKey("deck.id"), index=True)

    role:Mapped[EditorType] = mapped_column(SAEnum(EditorType),default=EditorType.viewer)

    joined_at:Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user:Mapped[User] = relationship(back_populates="user_memberships")
    deck:Mapped[Deck] = relationship(back_populates="deck_memberships")

