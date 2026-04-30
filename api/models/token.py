from sqlalchemy.orm import  Mapped,mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import INET
import uuid
from datetime import datetime
from typing import Optional

from api.db.database import Base 

class Token(Base):

    __tablename__ = "token"

    id:Mapped[int] = mapped_column(primary_key = True, index =True)
    jti:Mapped[uuid.UUID] = mapped_column(index=True, unique=True)
    refresh_token_hash:Mapped[str]
    revoked:Mapped[bool] = mapped_column(default=False)
    family_id:Mapped[uuid.UUID] = mapped_column(index=True)
    replaced_by_jti:Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    expires_at:Mapped[datetime] 
    created_at :Mapped[datetime] = mapped_column(default=datetime.utcnow)
    revoked_at:Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ip_address:Mapped[Optional[str]] = mapped_column(INET, nullable=True)

    user_id:Mapped[int] = mapped_column(ForeignKey("users.id"))