from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

from app.config import settings
from app.database import get_database_session, create_tables, close_database
from app.models import (
    EmailSubmissionRequest, 
    EmailSubmissionResponse, 
    HealthCheckResponse
)
from app.services import EmailService

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
    logger.info("Starting Eindr Email Capture API...")
    await create_tables()
    logger.info("Database tables created/verified")
    yield
    # Shutdown
    logger.info("Shutting down Eindr Email Capture API...")
    await close_database()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Backend API for capturing email addresses from the Eindr landing page",
    version="1.0.0",
    lifespan=lifespan
)

# Add HTTPS redirect middleware for production
if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
    """
    Submit an email address for the Eindr landing page
    
    Args:
        email_request: Email submission request containing the email address
        db: Database session dependency
        
    Returns:
        EmailSubmissionResponse with success status and message
    """
    try:
        logger.info(f"Received email submission request: {email_request.email}")
        
        result = await EmailService.submit_email(email_request, db)
        
        # Log the result
        if result.success:
            logger.info(f"Email submission successful: {email_request.email}")
        else:
            logger.warning(f"Email submission failed: {email_request.email}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in submit_email endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your request"
        )


@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_database_session)):
    """
    Get basic statistics about email submissions
    
    Args:
        db: Database session dependency
        
    Returns:
        Basic statistics about the email submissions
    """
    try:
        total_emails = await EmailService.get_email_count(db)
        
        return {
            "total_emails": total_emails,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching statistics"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment == "development"
    ) 