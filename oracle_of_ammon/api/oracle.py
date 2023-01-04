from io import BytesIO
import os
import sys

from fastapi import UploadFile
from haystack import Answer
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import EmbeddingRetriever
from haystack.pipelines import FAQPipeline
import pandas as pd

from oracle_of_ammon.common.logger import logger


class Oracle:
    def __init__(self, index: str = "document"):
        self.index = index
        self.use_gpu: bool = False
        self.document_store = self.create_document_store()
        self.retriever = self.create_retriever()
        self.pipeline = FAQPipeline(retriever=self.retriever)

        self.initialize_document_store()

    def create_document_store(self) -> InMemoryDocumentStore:
        try:
            return InMemoryDocumentStore(
                index=self.index,
                use_gpu=self.use_gpu,
                embedding_field="question_emb",
                embedding_dim=384,
                duplicate_documents="skip",
                similarity="cosine",
                progress_bar=False,
            )
        except Exception as e:
            logger.error(f"Unable to create document store: {e}")
            sys.exit(1)

    def create_retriever(self) -> EmbeddingRetriever:
        try:
            return EmbeddingRetriever(
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                document_store=self.document_store,
                use_gpu=self.use_gpu,
                scale_score=False,
                progress_bar=False,
            )
        except Exception as e:
            logger.error(f"Unable to create retriever: {e}")
            sys.exit(1)

    def index_documents(self, data: BytesIO | str) -> None:
        df: pd.DataFrame = pd.read_csv(filepath_or_buffer=data)

        if df.empty:
            raise RuntimeError("Dataframe is empty. Check filepath is correct.")

        logger.debug("Indexing documents...")

        questions = list(df["question"].values)
        df["question_emb"] = self.retriever.embed_queries(queries=questions).tolist()
        df = df.rename(columns={"question": "content"})

        try:
            docs_to_index = df.to_dict(orient="records")
            self.document_store.write_documents(
                docs_to_index, duplicate_documents="skip"
            )
        except Exception as e:
            logger.warning(f"Unable to write documents to document store: {e}")

    def upload_documents(self, files: list[UploadFile]) -> dict:
        for file in files:
            try:
                if ".csv" not in file.filename:
                    logger.warning("No files selected.")
                    return {"message": "No files selected."}

                self.index_documents(data=file.file)

            except Exception as exc:
                logger.error(f"Unable to upload {file.filename}: {exc}")
                return {"message": f"Unable to upload {file.filename}"}

            finally:
                file.file.close()

        logger.debug(f"Successfully uploaded {[file.filename for file in files]}")
        return {"message": f"Successfully uploaded {[file.filename for file in files]}"}

    def initialize_document_store(self) -> None:
        DIR: str = os.getenv("OASIS_OF_SIWA")
        if DIR is not None:
            try:
                self.index_documents(data=DIR)

            except Exception as e:
                logger.error(f"Unable to create dataframe from CSV: {e}")

        else:
            logger.debug("Initializing empty document store.")

    def search(self, query: str, params: dict = {"Retriever": {"top_k": 2}}) -> Answer:
        try:
            return self.pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")
