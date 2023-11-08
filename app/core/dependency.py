from database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError


def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
