from typing import Generic, TypeVar
from pydantic import Field
from app.core.schemas.base import BaseResponse


T = TypeVar("T")


class DataResponse(BaseResponse, Generic[T]):
    data: T = Field(..., description="Response data")
