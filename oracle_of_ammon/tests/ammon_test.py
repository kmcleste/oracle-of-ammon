import os
import pathlib

from fastapi.testclient import TestClient
from pydantic import parse_obj_as
from httpx import Response

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
    response: Response = client.get("/")
    assert response.status_code == 200


def test_health():
    response: Response = client.get("/health")
    assert response.status_code == 200
    assert parse_obj_as(HealthResponse, response.json())


def test_get_documents():
    response: Response = client.post(
        "/get-documents", json={"index": "document", "is_faq": True}
    )
    assert response.status_code == 200
    assert parse_obj_as(Documents, response.json())


def test_summary_empty_docstore():
    response: Response = client.post(
        "/summary", json={"index": "document", "is_faq": True}
    )
    assert response.status_code == 404
    assert parse_obj_as(HTTPError, response.json())


def test_faq_upload():
    file = open(
        file=pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "faq.csv"), mode="br"
    )
    response: Response = client.post(
        "/upload-documents",
        files={"files": file},
        json={"index": "document", "is_faq": True},
    )
    assert response.status_code == 201
    file.close()


def test_semantic_upload():
    file = open(
        file=pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "semantic.txt"),
        mode="br",
    )
    response: Response = client.post(
        "/upload-documents",
        files={"files": file},
        json={"index": "document", "is_faq": False},
    )
    assert response.status_code == 201
    file.close()


def test_summary():
    response: Response = client.post(
        "/summary", json={"index": "document", "is_faq": False}
    )
    assert response.status_code == 200
    assert parse_obj_as(Summary, response.json())


def test_faq_search():
    response: Response = client.post(
        "/faq-search",
        json={
            "query": "Why are duplicate answers being returned?",
            "params": {"Retriever": {"top_k": 10}},
        },
    )
    assert response.status_code == 200
    assert parse_obj_as(SearchResponse, response.json())


def test_extractive_search():
    response: Response = client.post(
        "/extractive-search",
        json={
            "query": "How for is Siwa from Memphis?",
            "params": {"Retriever": {"top_k": 3}, "Reader": {"top_k": 3}},
        },
    )
    assert response.status_code == 200
    assert parse_obj_as(SearchResponse, response.json())


def test_document_search():
    response: Response = client.post(
        "/document-search",
        json={
            "query": "Location of Ammon",
            "params": {"Retriever": {"top_k": 3}},
        },
    )
    assert response.status_code == 200
    assert parse_obj_as(Documents, response.json())
