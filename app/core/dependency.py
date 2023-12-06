from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
