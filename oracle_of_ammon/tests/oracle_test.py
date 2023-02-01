import os
import pathlib

from oracle_of_ammon.api.oracle import Oracle

oracle = Oracle()


def test_oracle_init():
    assert hasattr(oracle, "faq_document_store")
    assert hasattr(oracle, "semantic_document_store")
    assert hasattr(oracle, "faq_retriever")
    assert hasattr(oracle, "semantic_retriever")
    assert hasattr(oracle, "faq_pipeline")
    assert hasattr(oracle, "extractive_pipeline")
    assert hasattr(oracle, "document_search_pipeline")


def test_index_faq():
    path = pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "faq.csv").as_posix()
    oracle.index_documents(filepath_or_buffer=path, **{"is_faq": True})
    assert oracle.faq_document_store.get_document_count() != 0


def test_index_documents():
    path = pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "semantic.txt").as_posix()
    oracle.index_documents(filepath_or_buffer=path, **{"is_faq": False})
    assert oracle.semantic_document_store.get_document_count() != 0


def test_faq_search():
    assert oracle.faq_search(query="Why are duplicate questions being returned?")


def test_extractive_search():
    assert oracle.extractive_search(query="How far is Siwa from Memphis?")


def test_document_search():
    assert oracle.document_search(query="Climate of Ammon")
