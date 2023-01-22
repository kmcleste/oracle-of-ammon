#!/usr/bin/env python

import logging
import os

from fastapi import FastAPI, status, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn

from oracle_of_ammon.api.oracle import Oracle
from oracle_of_ammon.api.health import get_health_status
from oracle_of_ammon.api.models import (
    Search,
    SearchResponse,
    HealthResponse,
    UploadedDocuments,
    Summary,
    HTTPError,
    Documents,
    Index,
)
from oracle_of_ammon.utils.logger import configure_logger

logger: logging.Logger = configure_logger()


app = FastAPI(title=os.environ.get("API_TITLE", "Oracle of Ammon"), version="0.1.6")

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
    return oracle.faq_search(query=input.query, params=input.params)


@app.post(
    path="/extractive-search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
)
def extractive_search(input: Search):
    return oracle.extractive_search(query=input.query, params=input.params)


@app.post(
    path="/document-search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=Documents,
)
def document_search(input: Search):
    return oracle.document_search(query=input.query, params=input.params)


@app.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    response_model=HealthResponse,
)
def health():
    return get_health_status()


@app.post(
    path="/get-documents",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    # response_model=Documents,
)
def get_documents(input: Index):
    return {
        "faq": {
            "documents": oracle.faq_document_store.get_all_documents(
                index=input.index, return_embedding=False
            )
        },
        "semantic": {
            "documents": oracle.semantic_document_store.get_all_documents(
                index=input.index, return_embedding=False
            )
        },
    }


@app.post(
    path="/upload-documents",
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
    response_model=UploadedDocuments,
)
def upload_documents(
    files: list[UploadFile] = File(..., description="List of files to be indexed."),
    index: str = Query(
        default=os.environ.get("INDEX", "document"),
        description="Name of the desired index.",
    ),
    sheet_name: str
    | None = Query(
        "sheet_name",
        description="The sheet name(s) to index when uploading an XLSX file. Expects comma-separated string.",
    ),
    is_faq: bool = Query(
        False,
        description="Flag for if the uploaded content is intended to be used for FAQ.",
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
    if input.index not in oracle.document_store.indexes.keys():
        raise HTTPException(status_code=404, detail="Selected index does not exist.")
    if oracle.document_store.get_document_count() < 1:
        raise HTTPException(status_code=404, detail="Document store is empty.")
    return oracle.document_store.describe_documents(index=input.index)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
