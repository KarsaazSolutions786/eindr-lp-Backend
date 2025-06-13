from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

from app.database_psycopg import get_database_session, create_tables, close_database, Email
from app.models import EmailSubmissionRequest, EmailSubmissionResponse, HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    logger.info("Starting Eindr Email Capture API with PostgreSQL...")
    try:
        await create_tables()
        logger.info("PostgreSQL database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    yield
    # Shutdown
    logger.info("Shutting down Eindr Email Capture API...")
    await close_database()


# Create FastAPI app
app = FastAPI(
    title="Eindr Email Capture API",
    description="Backend API for capturing email addresses from the Eindr landing page (PostgreSQL)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In development, allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later."
        }
    )


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint for health check"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/submit-email", response_model=EmailSubmissionResponse)
async def submit_email(
    email_request: EmailSubmissionRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Submit an email address for the Eindr landing page"""
    try:
        logger.info(f"Received email submission request: {email_request.email}")
        
        # Check if email already exists
        query = select(Email).where(Email.email == email_request.email.lower().strip())
        result = await db.execute(query)
        existing_email = result.scalar_one_or_none()
        
        if existing_email:
            logger.info(f"Email already exists: {email_request.email}")
            return EmailSubmissionResponse(
                success=True,
                message="Email already registered. Thank you for your interest!",
                email_id=str(existing_email.id)
            )
        
        # Create new email record
        new_email = Email(email=email_request.email.lower().strip())
        db.add(new_email)
        await db.commit()
        await db.refresh(new_email)
        
        logger.info(f"New email submitted successfully to PostgreSQL: {email_request.email}")
        return EmailSubmissionResponse(
            success=True,
            message="Email successfully registered. We'll keep you updated!",
            email_id=str(new_email.id)
        )
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error: {e}")
        return EmailSubmissionResponse(
            success=True,  # Still return success for user experience
            message="Email already registered. Thank you for your interest!"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in submit_email endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your request"
        )


@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_database_session)):
    """Get basic statistics about email submissions"""
    try:
        query = select(Email)
        result = await db.execute(query)
        emails = result.scalars().all()
        total_emails = len(emails)
        
        return {
            "total_emails": total_emails,
            "timestamp": datetime.utcnow(),
            "storage_type": "PostgreSQL Database",
            "database": "eindr_lp"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching statistics"
        )


@app.get("/emails")
async def list_emails(db: AsyncSession = Depends(get_database_session)):
    """List all stored emails (for demo purposes)"""
    try:
        query = select(Email).order_by(Email.created_at.desc())
        result = await db.execute(query)
        emails = result.scalars().all()
        
        email_list = [
            {
                "id": str(email.id),
                "email": email.email,
                "created_at": email.created_at.isoformat()
            }
            for email in emails
        ]
        
        return {
            "emails": email_list,
            "total": len(email_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing emails: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching emails"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(
        "app.main_postgresql:app",
        host="0.0.0.0",
        port=port,
        reload=True
    ) 