import os
import pathlib

from fastapi import UploadFile

from oracle_of_ammon.api.oracle import Oracle

oracle = Oracle()


def test_oracle_init():
    assert hasattr(oracle, "preprocessor")
    assert hasattr(oracle, "faq_document_store")
    assert hasattr(oracle, "semantic_document_store")
    assert hasattr(oracle, "faq_retriever")
    assert hasattr(oracle, "semantic_retriever")
    assert hasattr(oracle, "faq_pipeline")
    assert hasattr(oracle, "extractive_pipeline")
    assert hasattr(oracle, "document_search_pipeline")
    assert hasattr(oracle, "reader")
    assert hasattr(oracle, "summarizer")
    assert hasattr(oracle, "document_merger")
    assert hasattr(oracle, "file_type_classifier")
    assert hasattr(oracle, "pdf_converter")
    assert hasattr(oracle, "markdown_converter")
    assert hasattr(oracle, "docx_converter")
    assert hasattr(oracle, "search_summarization_pipeline")
    assert hasattr(oracle, "span_summarizer_pipeline")
    assert hasattr(oracle, "indexing_pipeline")


def test_index_faq():
    path = pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "faq.csv").as_posix()
    oracle.index_documents(filepath_or_buffer=path, **{"is_faq": True})
    assert oracle.faq_document_store.get_document_count() != 0


def test_index_documents():
    path = pathlib.Path(
        os.getcwd(), "oracle_of_ammon", "data", "semantic.txt"
    ).as_posix()
    oracle.index_documents(
        filepath_or_buffer=path, filename="semantic.txt", **{"is_faq": False}
    )
    assert oracle.semantic_document_store.get_document_count() != 0


def test_faq_search():
    assert oracle.faq_search(query="Why are duplicate questions being returned?")


def test_extractive_search():
    assert oracle.extractive_search(query="How far is Siwa from Memphis?")


def test_document_search():
    assert oracle.document_search(query="Climate of Siwa?")


def test_search_summarization():
    assert oracle.search_summarization(query="What is the climate of Siwa?")


def test_document_summarization():
    file = open(
        pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "semantic.txt"), "br"
    )
    upload_file: UploadFile = UploadFile(filename="semantic.txt", file=file)
    assert oracle.document_summarization(file=upload_file)
    file.close()


def test_search_span_summarization():
    assert oracle.search_span_summarization(query="Who is Ammon?")
