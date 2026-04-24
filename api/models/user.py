from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from api.db.database import Base

class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(40))
    lastname:Mapped[str] = mapped_column(String(40))
    username: Mapped[str] = mapped_column(unique =True)
    email:Mapped[str] = mapped_column(unique=True)
    hashed_password:Mapped[str] 
    