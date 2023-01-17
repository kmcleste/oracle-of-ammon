import logging
import os
import sys

from fastapi import UploadFile
from haystack import Answer
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import EmbeddingRetriever
from haystack.pipelines import FAQPipeline, DocumentSearchPipeline
import pandas as pd
from tempfile import SpooledTemporaryFile

from oracle_of_ammon.api.utils.filehandler import FileHandler
from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()


class Oracle:
    def __init__(self, index: str = "document"):
        self.index = index
        self.use_gpu: bool = False
        self.document_store: InMemoryDocumentStore = self.create_document_store()
        self.retriever: EmbeddingRetriever = self.create_retriever()
        self.faq_pipeline: FAQPipeline = FAQPipeline(retriever=self.retriever)
        self.document_search_pipeline: DocumentSearchPipeline = DocumentSearchPipeline(
            retriever=self.retriever
        )

        self.index_documents()

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

    def index_documents(
        self,
        filepath_or_buffer: SpooledTemporaryFile
        | str = os.environ.get("OASIS_OF_SIWA", None),
        filename: str | None = None,
        index: str = "document",
        **kwargs,
    ) -> None:
        SHEET_NAME: str = kwargs.get("sheet_name", os.environ.get("SHEET_NAME", None))

        if SHEET_NAME is not None and filepath_or_buffer is None:
            logger.warning("A sheet name was provided but no excel file selected.")

        if SHEET_NAME is not None:
            SHEET_NAME = [x.strip() for x in SHEET_NAME.split(sep=",")]

        kwargs["sheet_name"] = SHEET_NAME

        if filepath_or_buffer is not None:
            df: pd.DataFrame = FileHandler.read_data(
                filepath_of_buffer=filepath_or_buffer, filename=filename, **kwargs
            )

            logger.debug("Indexing documents...")

            questions = list(df["question"].values)
            df["question_emb"] = self.retriever.embed_queries(
                queries=questions
            ).tolist()
            df = df.rename(columns={"question": "content"})

            try:
                docs_to_index = df.to_dict(orient="records")
                self.document_store.write_documents(
                    docs_to_index, duplicate_documents="skip", index=index
                )

            except Exception as e:
                logger.warning(f"Unable to write documents to document store: {e}")

    def upload_faq(
        self, files: list[UploadFile], index: str = "document", **kwargs
    ) -> dict:
        for file in files:
            try:
                self.index_documents(
                    filepath_or_buffer=file.file,
                    filename=file.filename,
                    index=index,
                    **kwargs,
                )

            except Exception as exc:
                logger.error(f"Unable to upload {file.filename}: {exc}")
                return {"message": f"Unable to upload {file.filename}"}

            finally:
                file.file.close()

        logger.debug(f"Successfully uploaded {[file.filename for file in files]}")
        return {"message": f"Successfully uploaded {[file.filename for file in files]}"}

    def faq_search(
        self,
        query: str,
        params: dict = {"Retriever": {"top_k": 3, "index": "document"}},
    ) -> Answer:
        try:
            return self.faq_pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")

    def document_search(
        self,
        query: str,
        params: dict = {"Retriever": {"top_k": 3, "index": "document"}},
    ) -> Answer:
        try:
            return self.document_search_pipeline.run(
                query=query, params=params, debug=False
            )
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")
