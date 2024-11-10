import time
from tests.utils import send_websocket_message


def test_convo_history_absent(client):
    # no ws connection, so no convo history available
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 0


def test_convo_history_update(client):
    message = "It's late! It's late!"

    # send websocket messages
    send_websocket_message({"text": message}, client)

    # check working memory update
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 2  # mex and reply
    assert json["history"][0]["who"] == "Human"
    assert json["history"][0]["message"] == message
    assert json["history"][0]["why"] == {}
    assert isinstance(json["history"][0]["when"], float)  # timestamp


def test_convo_history_reset(client):
    # send websocket messages
    send_websocket_message({"text": "It's late! It's late!"}, client)

    # delete convo history
    response = client.delete("/memory/conversation_history")
    assert response.status_code == 200

    # check working memory update
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 0


# TODO: should be tested also with concurrency!
def test_convo_history_by_user(client):
    convos = {
        # user_id: n_messages
        "White Rabbit": 2,
        "Alice": 3,
    }

    # send websocket messages
    for user_id, n_messages in convos.items():
        for m in range(n_messages):
            time.sleep(0.1)
            send_websocket_message(
                {"text": f"Mex n.{m} from {user_id}"}, client, user_id=user_id
            )

    # check working memories
    for user_id, n_messages in convos.items():
        response = client.get(
            "/memory/conversation_history/", headers={"user_id": user_id}
        )
        json = response.json()
        assert response.status_code == 200
        assert "history" in json
        assert len(json["history"]) == n_messages * 2  # mex and reply
        for m_idx, m in enumerate(json["history"]):
            assert "who" in m
            assert "message" in m
            if m_idx % 2 == 0:  # even message
                m_number_from_user = int(m_idx / 2)
                assert m["who"] == "Human"
                assert m["message"] == f"Mex n.{m_number_from_user} from {user_id}"
            else:
                assert m["who"] == "AI"

    # delete White Rabbit convo
    response = client.delete(
        "/memory/conversation_history/", headers={"user_id": "White Rabbit"}
    )
    assert response.status_code == 200

    # check convo deletion per user
    ### White Rabbit convo is empty
    response = client.get(
        "/memory/conversation_history/", headers={"user_id": "White Rabbit"}
    )
    json = response.json()
    assert len(json["history"]) == 0
    ### Alice convo still the same
    response = client.get(
        "/memory/conversation_history/", headers={"user_id": "Alice"}
    )
    json = response.json()
    assert len(json["history"]) == convos["Alice"] * 2



@pytest.mark.parametrize("index", [0,2,3,-1,-4])
def test_convo_history_edit(client, index):
    message1 = "It's late! It's late!"
    message2 = "We're all mad here."

    # send websocket messages
    send_websocket_message({"text": message1}, client)
    send_websocket_message({"text": message2}, client)

    response = client.get("/memory/conversation_history")
    # check the history memory is following:
    # history[0] -> "It's late! It's late!"
    # history[1] -> AI reply
    # history[2] -> "We're all mad here."
    # history[3] -> AI reply
    expected_history_size = 4
    json = response.json()
    assert "history" in json
    history = json["history"]
    assert len(history) == expected_history_size
    assert history[0]["message"] == message1
    assert history[2]["message"] == message2

    # overwrite history message1 using index
    req_json = {
        "who": "Human",
        "message": f"MIAO_{index}!",
        "why": {},
    }
    # if index is even set also role and when
    if index % 2 == 0:
        req_json["role"] = "Human"
        req_json["when"] = time.time()

    response = client.put(f"/memory/conversation_history/{index}",json=req_json)
    json = response.json()
    print(json)

    # check response
    assert response.status_code == 200
    params = ["who","message","why","role","when"] if index % 2 == 0 else ["who","message","why"]
    for p in params:
        assert json[p] == req_json[p]

    # check working memory update
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    history = json["history"]
    assert len(history) == expected_history_size

    for p in params:
     assert history[index][p] == req_json[p]


def test_convo_history_edit_wrong_index(client):
    message1 = "It's late! It's late!"
    message2 = "We're all mad here."

    # send websocket messages
    send_websocket_message({"text": message1}, client)
    send_websocket_message({"text": message2}, client)

    # overwrite history message1 using index out of range 4
    req_json1 = {
        "who": "Human",
        "message": "MIAO!",
        "why": {}
    }
    response = client.put("/memory/conversation_history/4",json=req_json1)
    assert "Index out of range. " in response.json()["detail"]["error"]

    # check response
    assert response.status_code == 400

    # overwrite history message1 using index out of range -5
    response = client.put("/memory/conversation_history/-5",json=req_json1)

    # check response
    assert response.status_code == 400
    assert "Index out of range. " in response.json()["detail"]["error"]
