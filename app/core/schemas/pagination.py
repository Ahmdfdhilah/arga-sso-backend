from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field
from app.core.schemas.base import BaseResponse


T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_prev_page: bool = Field(..., description="Whether there is a previous page")
    has_next_page: bool = Field(..., description="Whether there is a next page")


class PaginatedResponse(BaseResponse, Generic[T]):
    data: List[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
