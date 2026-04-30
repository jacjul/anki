from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import String
from typing import TYPE_CHECKING

from api.db.database import Base
if TYPE_CHECKING:
    from api.models.userdeck import UserDecks


class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(40))
    lastname:Mapped[str] = mapped_column(String(40))
    username: Mapped[str] = mapped_column(unique =True)
    email:Mapped[str] = mapped_column(unique=True)
    hashed_password:Mapped[str] 
    user_memberships:Mapped[list[UserDecks]] = relationship(back_populates="user")

