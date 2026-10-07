from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Shelf = Literal["WANT", "READING", "FINISHED"]


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    genre: str = "General"
    pages: int = Field(default=0, ge=0, le=20000)
    shelf: Shelf = "WANT"
    rating: int = Field(default=0, ge=0, le=5)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    genre: str | None = None
    pages: int | None = Field(default=None, ge=0, le=20000)
    shelf: Shelf | None = None
    rating: int | None = Field(default=None, ge=0, le=5)


class BookOut(BookCreate):
    id: int
    added_on: datetime
    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total: int
    want: int
    reading: int
    finished: int
    pagesRead: int
    averageRating: float
