#!/usr/bin/env python

import os
import pathlib
import sys
from typing import List

from fastapi import FastAPI, status, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

from oracle import Oracle
from health import get_health_status
from models import (
    Query,
    SearchResponse,
    HealthResponse,
    UploadedDocuments,
    Summary,
    HTTPError,
    Documents,
)

sys.path.append(
    str(
        pathlib.Path(
            pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent, "common"
        )
    )
)
from logger import logger


app = FastAPI(title="Oracle of Ammon", version="0.1.0")

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
    path="/search",
    status_code=status.HTTP_200_OK,
    tags=["search"],
    response_model=SearchResponse,
)
def search(input: Query):
    return oracle.search(query=input.query, params=input.params)


@app.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    response_model=HealthResponse,
)
def health():
    return get_health_status()


@app.get(
    path="/get-documents",
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    response_model=Documents,
)
def get_documents():
    return {
        "documents": oracle.document_store.get_all_documents(
            index=oracle.index, return_embedding=False
        )
    }


@app.post(
    path="/upload-documents",
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
    response_model=UploadedDocuments,
)
def upload_documents(
    files: list[UploadFile] = File(..., description="List of files to be indexed")
):
    return oracle.upload_documents(files=files)


@app.get(
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
def summary():
    if oracle.document_store.get_document_count() < 1:
        raise HTTPException(status_code=404, detail="Document store is empty.")
    return oracle.document_store.describe_documents(index=oracle.index)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
