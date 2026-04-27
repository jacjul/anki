from sqlalchemy.orm import  Mapped,mapped_column
from sqlalchemy import ForeignKey
from uuid import uuid5
from datetime import datetime

from api.db.database import Base 

class Token(Base):

    __tablename__ = "token"

    id:Mapped[int] = mapped_column(primary_key = True, index =True)
    jti:Mapped[str] = mapped_column(index=True, unique=True)
    refresh_token_hash:Mapped[str]
    revoked:Mapped[bool] = mapped_column(default=False)
    family_id:Mapped[str] = mapped_column(index=True)
    expires_at:Mapped[datetime] 
    created_at :Mapped[datetime] = mapped_column(default=datetime.now)
    revoked_at:Mapped[datetime] = mapped_column(nullable=True )

    user_id:Mapped[int] = mapped_column(ForeignKey("user.id"))