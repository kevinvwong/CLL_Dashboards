def test_root_returns_placeholder(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Initiative Dashboard Prototype" in response.text
