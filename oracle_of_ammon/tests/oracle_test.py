import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(os.getcwd(), "oracle_of_ammon", "api")))
from oracle import Oracle

oracle = Oracle()


def test_oracle_init():
    assert hasattr(oracle, "document_store")
    assert hasattr(oracle, "retriever")
    assert hasattr(oracle, "pipeline")


def test_index_documents():
    file = open(
        file=pathlib.Path(os.getcwd(), "oracle_of_ammon", "data", "test.csv"), mode="br"
    )
    oracle.index_documents(data=file)
    assert oracle.document_store.get_document_count() != 0
    file.close()


def test_search():
    assert oracle.search(query="This is a question.")
