#!/usr/bin/env python

import logging
import os
from typing import List, Union

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import HTMLResponse

from oracle_of_ammon.__version__ import __version__
from oracle_of_ammon.api.health import get_health_status
from oracle_of_ammon.api.models import (
    DocumentIDs,
    Documents,
    HealthResponse,
    HTTPError,
    Index,
    Search,
    SearchResponse,
    SearchSummary,
    Summary,
    UploadDelete,
)
from oracle_of_ammon.api.oracle import Oracle
from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()


app = FastAPI(title=os.environ.get("API_TITLE", "Oracle of Ammon"), version=__version__)

oracle = Oracle()


@app.get(path="/", include_in_schema=False)
async def root():
    content = """
        <style>
        body{
        background: rgba(0,0,0,0.9);
        }
        form{
        position: absolute;
        top: 50%;
        left: 50%;
        margin-top: -100px;
        margin-left: -250px;
        width: 500px;
        height: 200px;
        border: 4px dashed #fff;
        }
        form p{
        width: 100%;
        height: 100%;
        text-align: center;
        line-height: 170px;
        color: #ffffff;
        font-family: Arial;
        }
        form input{
        position: absolute;
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        outline: none;
        opacity: 0;
        }
        form button{
        margin: 0;
        color: #fff;
        background: #16a085;
        border: none;
        width: 508px;
        height: 35px;
        margin-top: -20px;
        margin-left: -4px;
        border-radius: 4px;
        border-bottom: 4px solid #117A60;
        transition: all .2s ease;
        outline: none;
        }
        form button:hover{
        background: #149174;
            color: #0C5645;
        }
        form button:active{
        border:0;
        }
        </style>
        <body>
        <form action="/upload-documents/" enctype="multipart/form-data" method="post">
            <input name="files" type="file" multiple>
            <p>Drag and drop your files</p>
            <button type="submit">Upload</button>
        </form>
        </body>
    """
    return HTMLResponse(content=content)


@app.post(
    path="/faq-search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=SearchResponse,
)
def faq_search(input: Search):
    """Perform FAQ information retrieval. System expects full sentence questions."""
    return oracle.faq_search(query=input.query, params=input.params)


@app.post(
    path="/extractive-search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=SearchResponse,
)
def extractive_search(input: Search):
    """Perform extractive, semantic search. System expects full sentence questions."""
    return oracle.extractive_search(query=input.query, params=input.params)


@app.post(
    path="/document-search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=Documents,
)
def document_search(input: Search):
    """Returns full documents related to user query."""
    return oracle.document_search(query=input.query, params=input.params)


@app.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    response_model=HealthResponse,
)
def health():
    """Health check returns CPU, Memory, and GPU information."""
    return get_health_status()


@app.post(
    path="/get-documents",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    response_model=Documents,
)
def get_documents(input: Index):
    """Returns all documents in the selected index/document store."""
    if input.is_faq:
        return {
            "documents": oracle.faq_document_store.get_all_documents(
                index=input.index, return_embedding=False
            )
        }
    else:
        return {
            "documents": oracle.semantic_document_store.get_all_documents(
                index=input.index, return_embedding=False
            )
        }


@app.post(
    path="/upload-documents",
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
    response_model=UploadDelete,
)
def upload_documents(
    files: List[UploadFile] = File(..., description="List of files to be indexed."),
    index: str = Query(
        default=os.environ.get("INDEX", "document"),
        description="Name of the desired index.",
    ),
    sheet_name: Union[str, None] = Query(
        "sheet_name",
        description="The sheet name(s) to index when uploading an XLSX file. Expects comma-separated string.",
    ),
    is_faq: bool = Query(
        False,
        description="Which document store to access.",
    ),
):
    return oracle.upload_documents(
        files=files, index=index, **{"sheet_name": sheet_name, "is_faq": is_faq}
    )


@app.post(
    path="/summary",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    responses={
        200: {"model": Summary},
        404: {
            "model": HTTPError,
            "description": "Returned when document store is empty.",
        },
    },
)
def summary(input: Index):
    """Returns basic summary statistics for a given index."""
    if input.is_faq:
        if input.index not in oracle.faq_document_store.indexes.keys():
            raise HTTPException(
                status_code=404, detail="Selected index does not exist."
            )
        return oracle.faq_document_store.describe_documents(index=input.index)
    if not input.is_faq:
        if input.index not in oracle.semantic_document_store.indexes.keys():
            raise HTTPException(
                status_code=404, detail="Selected index does not exist."
            )
        return oracle.semantic_document_store.describe_documents(index=input.index)


@app.delete(
    path="/delete-documents",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    response_model=UploadDelete,
)
def delete_documents(input: DocumentIDs):
    """Deletes selected documents from an index. Expects comma-separated list of document id's."""
    if input.is_faq:
        oracle.faq_document_store.delete_documents(index=input.index, ids=input.ids)
        oracle.faq_document_store.update_embeddings(
            retriever=oracle.faq_retriever,
            index=input.index,
            update_existing_embeddings=False,
        )
        return {"message": f"Successfully deleted: {input.ids}"}
    if not input.is_faq:
        oracle.semantic_document_store.delete_documents(
            index=input.index, ids=input.ids
        )
        oracle.semantic_document_store.update_embeddings(
            retriever=oracle.semantic_retriever, index=input.index
        )
        return {"message": f"Successfully deleted: {input.ids}"}


@app.delete(
    path="/delete-index",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    responses={
        200: {"model": UploadDelete},
        404: {
            "model": HTTPError,
            "description": "Returned when document store is empty.",
        },
    },
)
def delete_index(input: Index):
    """Deletes entire index."""
    if input.is_faq:
        if input.index not in oracle.faq_document_store.indexes.keys():
            raise HTTPException(
                status_code=404, detail="Selected index does not exist."
            )
        oracle.faq_document_store.delete_index(index=input.index)
        return {"message": f"Successfully deleted '{input.index}' index."}
    if not input.is_faq:
        if input.index not in oracle.semantic_document_store.indexes.keys():
            raise HTTPException(
                status_code=404, detail="Selected index does not exist."
            )
        oracle.semantic_document_store.delete_index(index=input.index)
        return {"message": f"Successfully deleted '{input.index}' index."}


@app.post(
    path="/search-summarization",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=SearchSummary,
)
def search_summarization(input: Search):
    """Extends document search. Finds the most relevant documents and then returns a summary for each one."""
    return oracle.search_summarization(query=input.query, params=input.params)


@app.post(
    path="/document-summarization",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=Documents,
)
def document_summarization(
    file: UploadFile = File(..., description="File to be summarized.")
):
    """Skips indexing and returns a document summary."""
    return oracle.document_summarization(file=file)


@app.post(
    path="/search-span-summarization",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=Documents,
)
def search_span_summarization(input: Search):
    """Extends document search. Finds the most relevant documents and returns a single, combined summary."""
    return oracle.search_span_summarization(query=input.query, params=input.params)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
