from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The URL for your SQLite database file. This will create a file named reviews.db
DATABASE_URL = "sqlite:///./reviews.db"

# Create a SQLAlchemy engine
# check_same_thread=False is needed for SQLite when using FastAPI's default 
# asynchronous/threaded environment to prevent internal errors.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for your database models. 
# All models will inherit from this Base class.
Base = declarative_base()

# Dependency function to get a database session for each request.
# FastAPI uses this dependency injection pattern to manage connections.
def get_db():
    db = SessionLocal()
    try:
        # 'yield db' returns the session to the request handler
        yield db
    finally:
        # 'db.close()' ensures the connection is properly closed after the request finishes
        db.close()
