from sqlalchemy import select

from api.models.card import Card
from api.models.userdeck import UserDecks, EditorType


def test_owner_can_create_card(client, register_and_login, create_deck_for_user):
    owner = register_and_login("card_owner")
    deck = create_deck_for_user(owner, name="Card Deck", public=False)

    create = client.post(
        "/api/card/create",
        json={
            "frontside": "hello",
            "backside": "hallo",
            "deck_id": deck["id"],
        },
        headers=owner["auth_headers"],
    )

    assert create.status_code == 200
    assert create.json()["message"] == "Success"


def test_editor_can_create_card(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("card_owner_editor")
    editor = register_and_login("card_editor")
    deck = create_deck_for_user(owner, name="Editor Deck", public=False)

    db_session.add(
        UserDecks(
            user_id=editor["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.editor,
        )
    )
    db_session.commit()

    create = client.post(
        "/api/card/create",
        json={
            "frontside": "front",
            "backside": "back",
            "deck_id": deck["id"],
        },
        headers=editor["auth_headers"],
    )

    assert create.status_code == 200


def test_viewer_cannot_create_card(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("card_owner_viewer")
    viewer = register_and_login("card_viewer")
    deck = create_deck_for_user(owner, name="Viewer Deck", public=False)

    db_session.add(
        UserDecks(
            user_id=viewer["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.viewer,
        )
    )
    db_session.commit()

    create = client.post(
        "/api/card/create",
        json={
            "frontside": "front",
            "backside": "back",
            "deck_id": deck["id"],
        },
        headers=viewer["auth_headers"],
    )

    assert create.status_code == 403


def test_member_can_read_private_deck_cards(client, db_session, register_and_login, create_deck_for_user):
    owner = register_and_login("card_read_owner")
    member = register_and_login("card_read_member")
    deck = create_deck_for_user(owner, name="Private Read Deck", public=False)

    owner_create = client.post(
        "/api/card/create",
        json={
            "frontside": "A",
            "backside": "B",
            "deck_id": deck["id"],
        },
        headers=owner["auth_headers"],
    )
    assert owner_create.status_code == 200

    db_session.add(
        UserDecks(
            user_id=member["user"]["id"],
            deck_id=deck["id"],
            role=EditorType.viewer,
        )
    )
    db_session.commit()

    read_cards = client.get(f"/api/card/all/{deck['id']}", headers=member["auth_headers"])

    assert read_cards.status_code == 200
    body = read_cards.json()
    assert len(body) == 1
    assert body[0]["frontside"] == "A"


def test_non_member_cannot_read_private_deck_cards(client, register_and_login, create_deck_for_user):
    owner = register_and_login("card_private_owner")
    outsider = register_and_login("card_private_outsider")
    deck = create_deck_for_user(owner, name="Private No Access", public=False)

    create = client.post(
        "/api/card/create",
        json={
            "frontside": "A",
            "backside": "B",
            "deck_id": deck["id"],
        },
        headers=owner["auth_headers"],
    )
    assert create.status_code == 200

    read_cards = client.get(f"/api/card/all/{deck['id']}", headers=outsider["auth_headers"])

    assert read_cards.status_code == 403


def test_read_private_deck_returns_cards_with_response_model_shape(client, register_and_login, create_deck_for_user):
    owner = register_and_login("card_shape_owner")
    deck = create_deck_for_user(owner, name="Shape Deck", public=False)

    create = client.post(
        "/api/card/create",
        json={
            "frontside": "front text",
            "backside": "back text",
            "deck_id": deck["id"],
        },
        headers=owner["auth_headers"],
    )
    assert create.status_code == 200

    response = client.get(f"/api/card/all/{deck['id']}", headers=owner["auth_headers"])
    assert response.status_code == 200

    card = response.json()[0]
    assert set(card.keys()) == {
        "id",
        "frontside",
        "frontside_explain",
        "backside",
        "backside_explain",
        "audio_front",
        "audio_back",
        "deck_id",
    }
