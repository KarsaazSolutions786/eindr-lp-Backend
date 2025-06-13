from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.sql import func
import uuid
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration for Railway deployment
def get_database_url():
    """Get database URL with Railway compatibility"""
    # Railway automatically provides DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Railway typically provides postgres:// URLs, convert to postgresql+psycopg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif not database_url.startswith("postgresql+psycopg://"):
            # Ensure we're using the psycopg driver
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        logger.info(f"🐘 Using Railway PostgreSQL database")
        return database_url
    else:
        # Local development fallback
        local_url = "postgresql+psycopg://postgres:admin123@localhost/eindr_lp"
        logger.info(f"🔧 Using local PostgreSQL database for development")
        return local_url

DATABASE_URL = get_database_url()
logger.info(f"🔗 Database connection configured")

# Create async engine with better error handling
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Disable verbose SQL logging in production
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Validate connections before use
    )
    logger.info("✅ Database engine created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    raise

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
    """Create database tables with better error handling"""
    try:
        logger.info("🔨 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        # Don't raise the exception to allow the app to start
        # The app can still start and show helpful error messages
        logger.warning("⚠️  App will continue without database initialization")


async def close_database():
    """Close database connection"""
    try:
        await engine.dispose()
        logger.info("🔌 Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}") 