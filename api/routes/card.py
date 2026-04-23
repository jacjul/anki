from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm  import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.card import Card
from api.models.deck import Deck
from api.db.database import get_db
from api.schemas.card import CreateCard

card_router = APIRouter(prefix="/card")

@card_router.get("/all")
def get_all_cards(db:Session=Depends(get_db)):

    stmt = select(Card)

    result = db.execute(stmt).mappings().all()

    return [dict(card) for card in result]

@card_router.get("/all/{deck_id}")
def get_all_cards_deck(deck_id:int, db:Session=Depends(get_db)):
    stmt = select(Card).where(Card.deck_id ==deck_id)

    result = db.execute(stmt).mappings().all()

    return [dict(card) for card in result]

@card_router.post("/create")
def create_card(card:CreateCard, db:Session=Depends(get_db)):

    
    deck_exists = db.execute(select(Deck.id).where(Deck.id == card.deck_id)).scalar_one_or_none()

    if  deck_exists is None:
        raise HTTPException(status_code = 404, detail="Deck doesn't exist")
    
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
        return {"message":"Success"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code = 409,detail="Card could not be created to data error")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail = "DB-Error while creating Card")
        
      