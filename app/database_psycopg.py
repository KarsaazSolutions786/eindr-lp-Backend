from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.sql import func
import uuid
import os

# Database configuration with user's credentials
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:admin123@localhost/eindr_lp"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

print(f"🔗 Attempting to connect to PostgreSQL: {DATABASE_URL.replace('admin123', '***')}")

# Create async engine with psycopg
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable logging for debugging
    future=True
)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Dependency to get database session
async def get_database_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """Close database connection"""
    await engine.dispose() 