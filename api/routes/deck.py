from fastapi import APIRouter,Depends,HTTPException 
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, and_ 
from typing import Annotated

from api.db.database import get_db
from api.models.deck import Deck 
from api.models.user import User
from api.models.userdeck import UserDecks, EditorType
from api.schemas.deck import CreateDeck, UpdateDeck, ActionDeck, DeckResponse
from api.schemas.common import MessageResponse
from api.auth.user import get_current_user 
deck_router = APIRouter(prefix="/deck")

@deck_router.post("/create", response_model=DeckResponse)
def create_deck(deck: CreateDeck, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    deck_dict = deck.model_dump()
    new_deck = Deck(**deck_dict, owner=user)

    try:
        db.add(new_deck)
        db.flush()

        owner_membership = UserDecks(
            user_id=user.id,
            deck_id=new_deck.id,
            role=EditorType.owner,
        )
        db.add(owner_membership)

        db.commit()
        db.refresh(new_deck)
        return new_deck
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code = 500, detail="DB execute issue")
    
@deck_router.delete("/delete/{id}", response_model=MessageResponse)
def delete_deck(id: int, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):

    
    deck = db.execute(select(Deck).where(and_(Deck.id == id , Deck.owner_id ==user.id))).scalar_one_or_none()

    if deck is None:
        raise HTTPException(status_code=404, detail="Deck doesn't exist or you are not the owner of the deck")

    try:
        db.delete(deck)
        db.commit()
        return {"message": "Success"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="DB execute issue")
    
@deck_router.patch("/update/{action}", response_model=MessageResponse)
def update_deck(action: ActionDeck, deck: UpdateDeck, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):

    deck_row = db.execute(select(Deck).where(Deck.id == deck.id)).scalar_one_or_none()

    if deck_row is None:
        raise HTTPException(status_code=404, detail="Deck to update wasn't found")

    is_owner = deck_row.owner_id == user.id

    can_edit = db.execute(
        select(UserDecks.id).where(
            and_(
                UserDecks.deck_id == deck.id,
                UserDecks.user_id == user.id,
                UserDecks.role.in_([EditorType.owner, EditorType.editor]),
            )
        )
    ).scalar_one_or_none()

    if action == ActionDeck.RENAME:
        if not is_owner and can_edit is None:
            raise HTTPException(status_code=403, detail="You are not allowed to rename this deck")
        deck_row.name = deck.name.strip()

    elif action == ActionDeck.PUBLIC:
        if not is_owner:
            raise HTTPException(status_code=403, detail="Only the owner can change deck visibility")
        deck_row.public = deck.public
    else:
        raise HTTPException(400, detail="Invalid action")
    
    try:
        db.commit()
        db.refresh(deck_row)
        return {"message": "Success"}
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail="Deck update conflict")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "DB execute issue")
