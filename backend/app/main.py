from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Book
from .schemas import BookCreate, BookOut, BookUpdate, StatsOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    # the container runs alembic before uvicorn; create_all is here so the
    # tests can run against sqlite without a migration step
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(func.count(Book.id)))
    return {"status": "READY"}


@app.get("/api/books", response_model=list[BookOut])
def list_books(shelf: str | None = None, db: Session = Depends(get_db)):
    query = select(Book).order_by(Book.id.desc())
    if shelf:
        query = query.where(Book.shelf == shelf.upper())
    return list(db.scalars(query))


@app.get("/api/books/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Book.shelf, func.count(Book.id)).group_by(Book.shelf)
    ).all()
    counts = {shelf: count for shelf, count in rows}

    pages_read = db.scalar(
        select(func.coalesce(func.sum(Book.pages), 0)).where(Book.shelf == "FINISHED")
    )
    rated = list(db.scalars(select(Book.rating).where(Book.rating > 0)))
    average = round(sum(rated) / len(rated), 2) if rated else 0.0

    return StatsOut(
        total=sum(counts.values()),
        want=counts.get("WANT", 0),
        reading=counts.get("READING", 0),
        finished=counts.get("FINISHED", 0),
        pagesRead=pages_read or 0,
        averageRating=average,
    )


@app.get("/api/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/api/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.put("/api/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


@app.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
