import os
import pathlib

from oracle_of_ammon.api.oracle import Oracle

oracle = Oracle()


def test_oracle_init():
    assert hasattr(oracle, "document_store")
    assert hasattr(oracle, "retriever")
    assert hasattr(oracle, "faq_pipeline")
    assert hasattr(oracle, "document_search_pipeline")


def test_index_documents():
    path = pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "faq.csv").as_posix()
    oracle.index_documents(filepath_or_buffer=path)
    assert oracle.document_store.get_document_count() != 0


def test_faq_search():
    assert oracle.faq_search(query="Why are duplicate questions being returned?")


def test_document_search():
    assert oracle.document_search(query="Why are duplicate questions being returned?")
