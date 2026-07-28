from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)