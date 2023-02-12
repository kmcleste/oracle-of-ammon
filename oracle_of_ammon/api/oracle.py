import logging
import os
import sys
from tempfile import SpooledTemporaryFile
from typing import List, Union

import pandas as pd
from fastapi import UploadFile
from haystack import Answer
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import (
    DocumentMerger,
    DocxToTextConverter,
    EmbeddingRetriever,
    FARMReader,
    FileTypeClassifier,
    MarkdownConverter,
    PDFToTextConverter,
    PreProcessor,
    TextConverter,
    TransformersSummarizer,
)
from haystack.pipelines import (
    DocumentSearchPipeline,
    ExtractiveQAPipeline,
    FAQPipeline,
    Pipeline,
    SearchSummarizationPipeline,
)

from oracle_of_ammon.api.utils.filehandler import FileHandler
from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()


class Oracle:
    def __init__(self, index: str = os.environ.get("INDEX", "document")):
        self.index = index
        self.use_gpu: bool = False

        self.preprocessor: PreProcessor = self.create_preprocessor()
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
        self.document_merger: DocumentMerger = self.create_document_merger()
        self.text_converter: TextConverter = self.create_text_converter()
        self.file_type_classifier: FileTypeClassifier = (
            self.create_file_type_classifier()
        )
        self.pdf_converter: PDFToTextConverter = self.create_pdf_converter()
        self.markdown_converter: MarkdownConverter = self.create_markdown_converter()
        self.docx_converter: DocxToTextConverter = self.create_docx_converter()

        self.faq_pipeline: FAQPipeline = FAQPipeline(retriever=self.faq_retriever)
        self.extractive_pipeline: ExtractiveQAPipeline = ExtractiveQAPipeline(
            reader=self.reader, retriever=self.semantic_retriever
        )
        self.document_search_pipeline: DocumentSearchPipeline = DocumentSearchPipeline(
            retriever=self.semantic_retriever
        )
        self.search_summarization_pipeline: SearchSummarizationPipeline = (
            SearchSummarizationPipeline(
                summarizer=self.summarizer,
                retriever=self.semantic_retriever,
                generate_single_summary=False,
            )
        )
        self.span_summarizer_pipeline: Pipeline = self.create_span_summarizer_pipeline()
        self.indexing_pipeline: Pipeline = self.create_indexing_pipeline()

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
                progress_bar=True,
            )
            semantic: InMemoryDocumentStore = InMemoryDocumentStore(
                index=self.index,
                use_gpu=self.use_gpu,
                embedding_dim=768,
                duplicate_documents="skip",
                similarity="dot_product",
                progress_bar=True,
            )
            return faq, semantic

        except Exception as e:
            logger.critical(f"Unable to create document store: {e}")
            sys.exit(1)

    def create_retriever(self) -> EmbeddingRetriever:
        try:
            faq: EmbeddingRetriever = EmbeddingRetriever(
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                model_format="sentence_transformers",
                document_store=self.faq_document_store,
                use_gpu=self.use_gpu,
                scale_score=False,
                progress_bar=True,
            )
            semantic: EmbeddingRetriever = EmbeddingRetriever(
                embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
                model_format="sentence_transformers",
                document_store=self.semantic_document_store,
                use_gpu=self.use_gpu,
                scale_score=False,
                progress_bar=True,
            )

            return faq, semantic

        except Exception as e:
            logger.critical(f"Unable to create retriever: {e}")
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
            logger.critical(f"Unable to create reader: {e}")
            sys.exit(1)

    def create_summarizer(self) -> TransformersSummarizer:
        try:
            return TransformersSummarizer(
                model_name_or_path="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                max_length=250,
                min_length=30,
                use_gpu=self.use_gpu,
                progress_bar=True,
            )
        except Exception as e:
            logger.critical(f"Unable to create summarizer: {e}")
            sys.exit(1)

    def create_document_merger(self) -> DocumentMerger:
        try:
            return DocumentMerger(separator=" ")
        except Exception as e:
            logger.critical(f"Unable to create document merger: {e}")
            sys.exit(1)

    def create_span_summarizer_pipeline(self) -> Pipeline:
        try:
            pipeline: Pipeline = Pipeline()
            pipeline.add_node(
                component=self.semantic_retriever, name="Retriever", inputs=["Query"]
            )
            pipeline.add_node(
                component=self.document_merger,
                name="DocumentMerger",
                inputs=["Retriever"],
            )
            pipeline.add_node(
                component=self.summarizer, name="Summarizer", inputs=["DocumentMerger"]
            )

            return pipeline
        except Exception as e:
            logger.critical(f"Unable to create span summarizer pipeline: {e}")
            sys.exit(1)

    def create_preprocessor(self) -> PreProcessor:
        try:
            return PreProcessor(
                clean_empty_lines=True,
                clean_whitespace=True,
                clean_header_footer=True,
                split_by="word",
                split_length=200,
                split_respect_sentence_boundary=True,
                split_overlap=0,
            )
        except Exception as e:
            logger.critical(f"Unable to create preprocessor: {e}")
            sys.exit(1)

    def create_file_type_classifier(self) -> FileTypeClassifier:
        try:
            return FileTypeClassifier()
        except Exception as e:
            logger.critical(f"Unable to create file type classifier: {e}")
            sys.exit(1)

    def create_text_converter(self) -> TextConverter:
        try:
            return TextConverter(remove_numeric_tables=False, progress_bar=True)
        except Exception as e:
            logger.critical(f"Unable to create text converter: {e}")
            sys.exit(1)

    def create_pdf_converter(self) -> PDFToTextConverter:
        try:
            return PDFToTextConverter()
        except Exception as e:
            logger.critical(f"Unable to create pdf text converter: {e}")
            sys.exit(1)

    def create_markdown_converter(self) -> MarkdownConverter:
        try:
            return MarkdownConverter()
        except Exception as e:
            logger.critical(f"Unable to create markdown converter: {e}")
            sys.exit(1)

    def create_docx_converter(self) -> DocxToTextConverter:
        try:
            return DocxToTextConverter(
                remove_numeric_tables=False, valid_languages=["en"], progress_bar=True
            )
        except Exception as e:
            logger.critical(f"Unable to create docx converter: {e}")
            sys.exit(1)

    def create_base_document_pipeline(self) -> Pipeline:
        """Reusable function to create document handling pipelines."""
        try:
            pipeline: Pipeline = Pipeline()
            pipeline.add_node(
                component=self.file_type_classifier,
                name="FileTypeClassifier",
                inputs=["File"],
            )
            pipeline.add_node(
                component=self.text_converter,
                name="TextConverter",
                inputs=["FileTypeClassifier.output_1"],
            )
            pipeline.add_node(
                component=self.pdf_converter,
                name="PdfConverter",
                inputs=["FileTypeClassifier.output_2"],
            )
            pipeline.add_node(
                component=self.markdown_converter,
                name="MarkdownConverter",
                inputs=["FileTypeClassifier.output_3"],
            )
            pipeline.add_node(
                component=self.docx_converter,
                name="DocxConverter",
                inputs=["FileTypeClassifier.output_4"],
            )
            pipeline.add_node(
                component=self.preprocessor,
                name="PreProcessor",
                inputs=[
                    "TextConverter",
                    "PdfConverter",
                    "MarkdownConverter",
                    "DocxConverter",
                ],
            )
            return pipeline
        except Exception as e:
            logger.critical(f"Unable to create base document pipeline: {e}")
            sys.exit(1)

    def create_indexing_pipeline(self) -> Pipeline:
        try:
            pipeline: Pipeline = self.create_base_document_pipeline()
            pipeline.add_node(
                component=self.semantic_document_store,
                name="DocumentStore",
                inputs=["PreProcessor"],
            )
            return pipeline
        except Exception as e:
            logger.critical(f"Unable to create indexing pipeline: {e}")
            sys.exit(1)

    def create_summarization_pipeline(self) -> Pipeline:
        try:
            pipeline: Pipeline = self.create_base_document_pipeline()
            pipeline.add_node(
                component=self.document_merger,
                name="DocumentMerger",
                inputs=["PreProcessor"],
            )
            pipeline.add_node(
                component=self.summarizer, name="Summarizer", inputs=["DocumentMerger"]
            )

            return pipeline
        except Exception as e:
            logger.critical(f"Unable to create indexing pipeline: {e}")
            sys.exit(1)

    def index_documents(
        self,
        filepath_or_buffer: Union[SpooledTemporaryFile, str] = os.environ.get(
            "OASIS_OF_SIWA", None
        ),
        filename: Union[str, None] = None,
        index: str = os.environ.get("INDEX", "document"),
        **kwargs,
    ) -> None:
        is_faq = os.environ.get("IS_FAQ") == "True"
        if kwargs.get("is_faq", is_faq) and filepath_or_buffer:
            SHEET_NAME: str = kwargs.get(
                "sheet_name", os.environ.get("SHEET_NAME", None)
            )

            if SHEET_NAME is not None and filepath_or_buffer is None:
                logger.warning("A sheet name was provided but no excel file selected.")

            try:
                if SHEET_NAME is not None:
                    SHEET_NAME = [x.strip() for x in SHEET_NAME.split(sep=",")]
            except Exception as e:
                logger.error(f"Unable to process xlsx sheet names: {e}")

            kwargs["sheet_name"] = SHEET_NAME

            if filepath_or_buffer is not None:
                df: pd.DataFrame = FileHandler.read_faq(
                    filepath_or_buffer=filepath_or_buffer, filename=filename, **kwargs
                )

                logger.debug("Indexing documents...")

                questions = list(df["question"].values)
                df["question_emb"] = self.faq_retriever.embed_queries(
                    queries=questions
                ).tolist()
                df = df.rename(columns={"question": "content"})

                try:
                    docs_to_index = df.to_dict(orient="records")
                    self.faq_document_store.write_documents(
                        docs_to_index, duplicate_documents="skip", index=index
                    )

                except Exception as e:
                    logger.warning(f"Unable to write documents to document store: {e}")
        elif not kwargs.get("is_faq", is_faq) and filepath_or_buffer:
            path, meta = FileHandler.read_documents(
                filepath_or_buffer=filepath_or_buffer,
                filename=filename,
            )
            self.indexing_pipeline.run(file_paths=[path], meta=[meta])

            FileHandler.file_clean_up(path=path)

            self.semantic_document_store.update_embeddings(
                retriever=self.semantic_retriever,
                index=index,
                update_existing_embeddings=False,
            )

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
        params: dict = {
            "Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}
        },
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
        params: dict = {
            "Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}
        },
    ) -> Answer:
        try:
            return self.document_search_pipeline.run(
                query=query, params=params, debug=False
            )
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")

    def search_summarization(
        self,
        query: str,
        params: dict = {
            "Retriever": {"top_k": 5, "index": os.environ.get("INDEX", "document")}
        },
    ):
        try:
            return self.search_summarization_pipeline.run(
                query=query, params=params, debug=False
            )
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")

    def search_span_summarization(
        self,
        query: str,
        params: dict = {
            "Retriever": {"top_k": 5, "index": os.environ.get("INDEX", "document")}
        },
    ):
        try:
            return self.span_summarizer_pipeline.run(
                query=query, params=params, debug=False
            )
        except Exception as e:
            logger.error(f"Unable to perform query: {e}")

    def document_summarization(self, file: UploadFile) -> dict:
        try:
            path, meta = FileHandler.read_documents(
                filepath_or_buffer=file.file, filename=file.filename
            )
            pipeline = self.create_summarization_pipeline()

            return pipeline.run(file_paths=[path], meta=[meta])

        except Exception as exc:
            logger.error(f"Unable to upload {file.filename}: {exc}")
            return {"message": f"Unable to upload {file.filename}"}

        finally:
            file.file.close()
