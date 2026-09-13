import api as sut
from fastapi import FastAPI
from fastapi.testclient import TestClient


client = TestClient(sut.app)


def test_api():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
