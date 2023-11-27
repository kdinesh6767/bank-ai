from sqlalchemy.orm import Session
from database import SessionLocal, init_db

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close
#  function to initialize the database:
def initialize_database():
    init_db()