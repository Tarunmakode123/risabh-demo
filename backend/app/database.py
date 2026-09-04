from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import settings

# Setup SQLAlchemy Database Engine with StaticPool for in-memory SQLite safety
if "sqlite" in settings.DATABASE_URL:
    kwargs = {"check_same_thread": False}
    if ":memory:" in settings.DATABASE_URL:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args=kwargs,
            poolclass=StaticPool
        )
    else:
        engine = create_engine(settings.DATABASE_URL, connect_args=kwargs)
else:
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    # Ensure database schema tables exist on cold-start instances
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
