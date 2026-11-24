from qums_fetch import Client


def test_login_page_returns_a_challenge():
    client = Client("unused", "unused", auto_login=False)
    challenge = client.fetch_login_challenge()

    assert challenge.token
    assert challenge.image_mime.startswith("image/")
    assert challenge.image_bytes
