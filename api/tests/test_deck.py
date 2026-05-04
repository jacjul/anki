from sqlalchemy import select

from api.models.deck import Deck
from api.models.userdeck import UserDecks, EditorType


def test_create_deck_creates_owner_membership(client, db_session, register_and_login):
    owner = register_and_login("owner")

    create = client.post(
        "/api/deck/create",
        json={"name": "Owner Deck", "public": False},
        headers=owner["auth_headers"],
    )

    assert create.status_code == 200
    deck = create.json()

    membership = db_session.execute(
        select(UserDecks).where(
            UserDecks.deck_id == deck["id"],
            UserDecks.user_id == owner["user"]["id"],
        )
    ).scalar_one_or_none()

    assert membership is not None
    assert membership.role == EditorType.owner


def test_editor_can_rename_deck(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("owner_rename")
    editor = register_and_login("editor_rename")

    deck = create_deck_for_user(owner, name="Before Rename", public=False)

    db_session.add(
        UserDecks(
            user_id=editor["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.editor,
        )
    )
    db_session.commit()

    rename = client.patch(
        "/api/deck/update/rename",
        json={"id": deck["id"], "name": "After Rename", "public": False},
        headers=editor["auth_headers"],
    )

    assert rename.status_code == 200

    updated = db_session.execute(select(Deck).where(Deck.id == deck["id"])).scalar_one()
    assert updated.name == "After Rename"


def test_editor_cannot_change_visibility(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("owner_visibility")
    editor = register_and_login("editor_visibility")

    deck = create_deck_for_user(owner, name="Visibility Deck", public=False)

    db_session.add(
        UserDecks(
            user_id=editor["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.editor,
        )
    )
    db_session.commit()

    change_visibility = client.patch(
        "/api/deck/update/public",
        json={"id": deck["id"], "name": deck["name"], "public": True},
        headers=editor["auth_headers"],
    )

    assert change_visibility.status_code == 403


def test_editor_cannot_delete_owner_deck(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("owner_delete")
    editor = register_and_login("editor_delete")

    deck = create_deck_for_user(owner, name="Delete Deck", public=False)

    db_session.add(
        UserDecks(
            user_id=editor["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.editor,
        )
    )
    db_session.commit()

    deletion = client.delete(f"/api/deck/delete/{deck['id']}", headers=editor["auth_headers"])

    assert deletion.status_code == 404
