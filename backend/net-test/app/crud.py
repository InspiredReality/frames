from sqlalchemy.orm import Session
from .models import Counter

def get_counter(db: Session):
    return db.query(Counter).first()

def create_counter(db: Session):
    counter = Counter(value=0)
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return counter

def increment_counter(db: Session):
    counter = get_counter(db)
    counter.value += 1
    db.commit()
    db.refresh(counter)
    return counter.value
