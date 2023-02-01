import logging
import os
import sys
from tempfile import SpooledTemporaryFile
from typing import List, Union

import pandas as pd
from fastapi import UploadFile
from haystack import Answer, Document
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import (
    EmbeddingRetriever,
    FARMReader,
    PreProcessor,
    TransformersSummarizer,
)
from haystack.pipelines import (
    DocumentSearchPipeline,
    ExtractiveQAPipeline,
    FAQPipeline,
    SearchSummarizationPipeline,
)

from oracle_of_ammon.api.utils.filehandler import FileHandler
from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()


class Oracle:
    def __init__(self, index: str = os.environ.get("INDEX", "document")):
        self.index = index
        self.use_gpu: bool = False

        self.preprocessor: PreProcessor = PreProcessor(
            clean_empty_lines=True,
            clean_whitespace=True,
            clean_header_footer=True,
            split_by="word",
            split_length=200,
            split_respect_sentence_boundary=True,
            split_overlap=0,
        )

        self.faq_document_store: InMemoryDocumentStore
        self.semantic_document_store: InMemoryDocumentStore
        (
            self.faq_document_store,
            self.semantic_document_store,
        ) = self.create_document_store()

        self.faq_retriever: EmbeddingRetriever
        self.semantic_retriever: EmbeddingRetriever
        self.faq_retriever, self.semantic_retriever = self.create_retriever()

        self.reader: FARMReader = self.create_reader()

        self.summarizer: TransformersSummarizer = self.create_summarizer()

        self.faq_pipeline: FAQPipeline = FAQPipeline(retriever=self.faq_retriever)
        self.extractive_pipeline: ExtractiveQAPipeline = ExtractiveQAPipeline(
            reader=self.reader, retriever=self.semantic_retriever
        )
        self.document_search_pipeline: DocumentSearchPipeline = DocumentSearchPipeline(
            retriever=self.semantic_retriever
        )
        self.search_summarization_pipeline: SearchSummarizationPipeline = SearchSummarizationPipeline(
            summarizer=self.summarizer,
            retriever=self.semantic_retriever,
            generate_single_summary=False,
        )

        self.index_documents()

    def create_document_store(self) -> InMemoryDocumentStore:
        try:
            faq: InMemoryDocumentStore = InMemoryDocumentStore(
                index=self.index,
                use_gpu=self.use_gpu,
                embedding_field="question_emb",
                embedding_dim=384,
                duplicate_documents="skip",
                similarity="cosine",
                progress_bar=False,
            )
            semantic: InMemoryDocumentStore = InMemoryDocumentStore(
                index=self.index,
                use_gpu=self.use_gpu,
                embedding_dim=768,
                duplicate_documents="skip",
                similarity="dot_product",
                progress_bar=False,
            )
            return faq, semantic

        except Exception as e:
            logger.error(f"Unable to create document store: {e}")
            sys.exit(1)

    def create_retriever(self) -> EmbeddingRetriever:
        try:
            faq: EmbeddingRetriever = EmbeddingRetriever(
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                model_format="sentence_transformers",
                document_store=self.faq_document_store,
                use_gpu=self.use_gpu,
                scale_score=False,
                progress_bar=False,
            )
            semantic: EmbeddingRetriever = EmbeddingRetriever(
                embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
                model_format="sentence_transformers",
                document_store=self.semantic_document_store,
                use_gpu=self.use_gpu,
                scale_score=False,
                progress_bar=False,
            )

            return faq, semantic

        except Exception as e:
            logger.error(f"Unable to create retriever: {e}")
            sys.exit(1)

    def create_reader(self) -> FARMReader:
        try:
            return FARMReader(
                model_name_or_path="deepset/roberta-base-squad2",
                use_gpu=self.use_gpu,
                max_seq_len=386,
                doc_stride=128,
                batch_size=96,
            )
        except Exception as e:
            logger.error(f"Unable to create reader: {e}")
            sys.exit(1)

    def create_summarizer(self) -> TransformersSummarizer:
        try:
            return TransformersSummarizer(
                model_name_or_path="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                max_length=130,
                min_length=30,
                use_gpu=self.use_gpu,
                progress_bar=False,
                generate_single_summary=False,
            )
        except Exception as e:
            logger.error(f"Unable to create summarizer: {e}")
            sys.exit(1)

    def index_documents(
        self,
        filepath_or_buffer: Union[SpooledTemporaryFile, str] = os.environ.get("OASIS_OF_SIWA", None),
        filename: Union[str, None] = None,
        index: str = os.environ.get("INDEX", "document"),
        **kwargs,
    ) -> None:
        is_faq = os.environ.get("IS_FAQ") == "True"
        if kwargs.get("is_faq", is_faq) and filepath_or_buffer:
            SHEET_NAME: str = kwargs.get("sheet_name", os.environ.get("SHEET_NAME", None))

            if SHEET_NAME is not None and filepath_or_buffer is None:
                logger.warning("A sheet name was provided but no excel file selected.")

            if SHEET_NAME is not None:
                SHEET_NAME = [x.strip() for x in SHEET_NAME.split(sep=",")]

            kwargs["sheet_name"] = SHEET_NAME

            if filepath_or_buffer is not None:
                df: pd.DataFrame = FileHandler.read_faq(
                    filepath_or_buffer=filepath_or_buffer, filename=filename, **kwargs
                )

                logger.debug("Indexing documents...")

                questions = list(df["question"].values)
                df["question_emb"] = self.faq_retriever.embed_queries(queries=questions).tolist()
                df = df.rename(columns={"question": "content"})

                try:
                    docs_to_index = df.to_dict(orient="records")
                    self.faq_document_store.write_documents(docs_to_index, duplicate_documents="skip", index=index)

                except Exception as e:
                    logger.warning(f"Unable to write documents to document store: {e}")
        elif not kwargs.get("is_faq", is_faq) and filepath_or_buffer:
            documents: List[Document] = FileHandler.read_documents(
                preprocessor=self.preprocessor,
                filepath_or_buffer=filepath_or_buffer,
                filename=filename,
            )
            self.semantic_document_store.write_documents(documents=documents, index=index, duplicate_documents="skip")
            self.semantic_document_store.update_embeddings(
                retriever=self.semantic_retriever,
                index=index,
                update_existing_embeddings=False,
            )
        else:
            return

    def upload_documents(
        self,
        files: List[UploadFile],
        index: str = os.environ.get("INDEX", "document"),
        **kwargs,
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
        params: dict = {"Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}},
    ) -> Answer:
        try:
            return self.faq_pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform faq searc: {e}")

    def extractive_search(
        self,
        query: str,
        params: dict = {
            "Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")},
            "Reader": {"top_k": 3},
        },
    ) -> Answer:
        try:
            return self.extractive_pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform extractive search: {e}")

    def document_search(
        self,
        query: str,
        params: dict = {"Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}},
    ) -> Answer:
        try:
            return self.document_search_pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")

    def search_summarization(
        self,
        query: str,
        params: dict = {"Retriever": {"tok_k": 5, "index": os.environ.get("INDEX", "document")}},
    ):
        try:
            return self.search_summarization_pipeline.run(query=query, params=params, debug=False)
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")
