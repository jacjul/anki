from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm  import Session
from typing import Annotated

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.card import Card
from api.models.deck import Deck
from api.models.user import User 
from api.models.userdeck import UserDecks, EditorType
from api.auth.user import get_current_user
from api.db.database import get_db
from api.schemas.card import CreateCard, CardResponse
from api.schemas.common import MessageResponse

card_router = APIRouter(prefix="/card")



@card_router.get("/all/{deck_id}", response_model=list[CardResponse])
def get_all_cards_deck(deck_id: int, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    available_deck = db.execute(select(Deck).where(Deck.id == deck_id)).scalar_one_or_none()

    if available_deck is None:
        raise HTTPException(status_code=404, detail="Deck does not exist")

    if not available_deck.public and available_deck.owner_id != user.id:
        is_member = db.execute(
            select(UserDecks.id).where(
                and_(
                    UserDecks.deck_id == deck_id,
                    UserDecks.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if is_member is None:
            raise HTTPException(status_code=403, detail="You are not allowed to view this private deck")

    cards = db.execute(select(Card).where(Card.deck_id == deck_id)).scalars().all()
    return cards

@card_router.post("/create", response_model=MessageResponse)
def create_card(card: CreateCard, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):

    deck_exists = db.execute(select(Deck).where(Deck.id == card.deck_id)).scalar_one_or_none()

    if deck_exists is None:
        raise HTTPException(status_code = 404, detail="Deck doesn't exist")

    can_edit = db.execute(
        select(UserDecks.id).where(
            and_(
                UserDecks.deck_id == card.deck_id,
                UserDecks.user_id == user.id,
                UserDecks.role.in_([EditorType.owner, EditorType.editor]),
            )
        )
    ).scalar_one_or_none()

    if deck_exists.owner_id != user.id and can_edit is None:
        raise HTTPException(status_code=403, detail="You are not allowed to edit this deck")
    
    new_card = Card(frontside = card.frontside, 
                frontside_explain=card.frontside_explain,
                backside = card.backside,
                backside_explain = card.backside_explain,
                audio_front = card.audio_front,
                audio_back = card.audio_back,
                deck_id = card.deck_id)
    try:

        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        return {"message": "Success"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code = 409,detail="Card could not be created to data error")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail = "DB-Error while creating Card")
        
      