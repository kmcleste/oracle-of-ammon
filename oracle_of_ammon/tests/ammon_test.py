import os
import pathlib

from fastapi.testclient import TestClient
from pydantic import parse_obj_as

from oracle_of_ammon.api.ammon import app
from oracle_of_ammon.api.models import (
    HealthResponse,
    Documents,
    HTTPError,
    SearchResponse,
    Summary,
)

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert parse_obj_as(HealthResponse, response.json())


def test_get_documents():
    response = client.get("/get-documents")
    assert response.status_code == 200
    assert parse_obj_as(Documents, response.json())


def test_summary_empty_docstore():
    response = client.get("/summary")
    assert response.status_code == 404
    assert parse_obj_as(HTTPError, response.json())


def test_search():
    response = client.post(
        "/search",
        json={
            "query": "This is a question.",
            "params": {"Retriever": {"top_k": 10}},
        },
    )
    assert response.status_code == 200
    assert parse_obj_as(SearchResponse, response.json())


def test_upload():
    file = open(
        file=pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "test.csv"), mode="br"
    )
    response = client.post("/upload-documents", files={"files": file})
    assert response.status_code == 201
    file.close()


def test_summary():
    response = client.get("/summary")
    assert response.status_code == 200
    assert parse_obj_as(Summary, response.json())
