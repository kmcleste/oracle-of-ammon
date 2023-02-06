import os
from typing import List, Optional

from haystack import Answer, Document
from pydantic import BaseModel, Field, validator


class Index(BaseModel):
    index: str = Field(
        default=os.environ.get("INDEX", "document"),
        description="Name of the desired index.",
    )
    is_faq: bool = Field(default=False, description="Which document store to access.")


class Search(BaseModel):
    query: str = Field(..., description="Natural language question in sentence form.")
    params: dict = Field(
        {"Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}},
        description="Search Engine node component parameters.",
    )


class SearchResponse(BaseModel):
    query: str = Field(..., description="Query posed by the user.")
    answers: List[Answer] = Field(
        ..., description="List of answers in descending order by relevance score."
    )


class Documents(BaseModel):
    documents: List[Document]


class SearchSummary(Documents):
    params: dict = Field(
        {"Retriever": {"top_k": 3, "index": os.environ.get("INDEX", "document")}},
        description="Search Engine node component parameters.",
    )
    query: str = Field(..., description="Query posed by the user.")
    node_id: str = Field(..., description="Name of the responding node.")


class UploadDelete(BaseModel):
    message: str = Field(..., description="Status of upload or deletion of documents.")


class DocumentIDs(Index):
    ids: List[str] = Field(..., description="List of document IDs to be selected.`")


class Summary(BaseModel):
    count: int = Field(..., description="Count of documents in an index.")
    chars_mean: float = Field(
        ..., description="Mean characters across all documents in an index."
    )
    chars_max: int = Field(
        ..., description="Maximum characters in any 1 document across an index.."
    )
    chars_min: int = Field(
        ..., description="Minimum characters in any 1 document across an index."
    )
    chars_median: int = Field(
        ..., description="Median characters across all documents in an index."
    )


class HTTPError(BaseModel):
    detail: str = Field(
        ..., description="Message explaining the reason for HTTPException."
    )

    class Config:
        schema_extra = {"example": {"detail": "HTTPException raised."}}


class CPUUsage(BaseModel):
    used: float = Field(..., description="REST API average CPU usage in percentage.")

    @validator("used")
    @classmethod
    def used_check(cls, v) -> float:
        return round(v, 2)


class MemoryUsage(BaseModel):
    used: float = Field(..., description="REST API used memory in percentage.")

    @validator("used")
    @classmethod
    def used_check(cls, v) -> float:
        return round(v, 2)


class GPUUsage(BaseModel):
    kernel_usage: float = Field(..., description="GPU kernel usage in percentage.")
    memory_total: int = Field(..., description="Total GPU memory in megabytes.")
    memory_used: Optional[int] = Field(
        ..., description="REST API used GPU memory in megabytes."
    )

    @validator("kernel_usage")
    @classmethod
    def kernel_usage_check(cls, v) -> float:
        return round(v, 2)


class GPUInfo(BaseModel):
    index: int = Field(..., description="GPU index.")
    usage: GPUUsage = Field(..., description="GPU usage details.")


class HealthResponse(BaseModel):
    version: str = Field(..., description="Haystack version.")
    cpu: CPUUsage = Field(..., description="CPU usage details.")
    memory: MemoryUsage = Field(..., description="Memory usage details.")
    gpus: List[GPUInfo] = Field(default_factory=list, description="GPU usage details.")
