from fastapi import APIRouter,Depends,HTTPException 
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select

from api.db.database import get_db
from api.models.deck import Deck 
from api.schemas.deck import CreateDeck,UpdateDeck,ActionDeck
deck_router = APIRouter(prefix="deck")

@deck_router.post("/create")
def create_deck(deck:CreateDeck , db:Session = Depends(get_db)):
    new_deck = Deck(*deck)

    try:
        db.add(new_deck)
        db.commit()
        db.refresh(new_deck)
        return {"message": "Success"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code = 500, detail="DB execute issue")
    
@deck_router.delete("/delete/{id}")
def delete_deck(id:int, db:Session = Depends(get_db)):

    deck = db.execute(select(Deck).where(Deck.id == id)).scalar_one_or_none()

    if deck is None:
        raise HTTPException(status_code=404, detail="Deck doesn't exist")

    try:
        db.delete(deck)
        db.commit()
        return {"message":"Success"}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="DB execute issue")
    
@deck_router.patch("/update/{action}")
def update_deck(action:ActionDeck, deck:UpdateDeck, db:Session= Depends(get_db)):

    deck_row = db.execute(select(Deck).where(Deck.id ==deck.id)).scalar_one_or_none()

    if deck_row is None:
        raise HTTPException(status_code = 404, detail = "Deck to update wasnt found")
    
    if action== ActionDeck.RENAME:
        deck_row.name = deck.name.strip()

    elif action == ActionDeck.PUBLIC:
        deck_row.public = deck.public
    else:
        raise HTTPException(400, detail="Invalid action")
    
    try:
        db.commit()
        db.refresh(deck_row)
        return {"message":"Success"}
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail="Deck update conflict")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "DB execute issue")
