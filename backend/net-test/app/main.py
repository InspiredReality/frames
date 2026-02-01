import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from . import models, crud

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.get("/hit")
def hit(db: Session = Depends(get_db)):
    counter = crud.get_counter(db)
    if not counter:
        counter = crud.create_counter(db)

    value = crud.increment_counter(db)
    return {"counter": value}
