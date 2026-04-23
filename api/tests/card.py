import pytest

test_data =  [
        (
            "success",
            lambda deck_id: {
                "frontside": "hello",
                "frontside_explain": "means hello",
                "backside": "hallo",
                "backside_explain": "bedeutet hallo",
                "deck_id": deck_id,
            },
            200,
            None,
        ),
        (
            "deck_not_found",
            lambda deck_id: {
                "frontside": "hello",
                "backside": "hallo",
                "deck_id": -1,
            },
            404,
            "Deck doesn't exist",
        ),
        (
            "missing_required_field",
            lambda deck_id: {
                "backside": "hallo",
                "deck_id": deck_id,
            },
            422,
            None,
        ),
        (
            "wrong_type",
            lambda deck_id: {
                "frontside": "hello",
                "backside": "hallo",
                "deck_id": "not_an_int",
            },
            422,
            None,
        ),
    ]

@pytest.mark.parametrize("case_name, payload_builder, expected_status_code, expected_detail", test_data)
def test_create_card_cases(client, create_deck, case_name, payload_builder, expected_status_code, expected_detail):
    payload = payload_builder(create_deck)

    response = client.post("/api/card/create", json=payload)

    assert response.status_code == expected_status_code

    body = response.json()
    if response.status_code ==200:
        assert body.get("message") == "Success"
    if expected_detail is not None:
        assert body.get("detail") == expected_detail

    


