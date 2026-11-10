from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@127.0.0.1:55432/"
    "ai_operations_copilot"
)


engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
