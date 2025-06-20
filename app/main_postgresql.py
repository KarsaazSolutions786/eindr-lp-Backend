from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os
import secrets

from app.database_psycopg import get_database_session, create_tables, close_database, Email
from app.models import EmailSubmissionRequest, EmailSubmissionResponse, HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize HTTP Basic Auth
security = HTTPBasic()

# Authentication credentials
ADMIN_EMAIL = "admin@karsaaz.com"
ADMIN_PASSWORD = "Admin123"

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate admin user for protected endpoints"""
    is_correct_email = secrets.compare_digest(credentials.username, ADMIN_EMAIL)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_email and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Track database status
database_available = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    global database_available
    
    # Startup
    logger.info("🚀 Starting Eindr Email Capture API with PostgreSQL...")
    
    try:
        await create_tables()
        database_available = True
        logger.info("✅ Database initialization successful")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        database_available = False
        logger.warning("⚠️  API will start without database - check Railway PostgreSQL service")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Eindr Email Capture API...")
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
    """Health check endpoint with database status"""
    global database_available
    
    status = "healthy" if database_available else "degraded"
    
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database_status="connected" if database_available else "disconnected"
    )


@app.post("/submit-email", response_model=EmailSubmissionResponse)
async def submit_email(
    email_request: EmailSubmissionRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Submit an email address for the Eindr landing page"""
    global database_available
    
    if not database_available:
        logger.warning("Database not available, returning error response")
        raise HTTPException(
            status_code=503,
            detail="Database service is currently unavailable. Please try again later."
        )
    
    try:
        logger.info(f"📧 Received email submission: {email_request.email}")
        
        # Check if email already exists
        query = select(Email).where(Email.email == email_request.email.lower().strip())
        result = await db.execute(query)
        existing_email = result.scalar_one_or_none()
        
        if existing_email:
            logger.info(f"🔄 Email already exists: {email_request.email}")
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
        
        logger.info(f"✅ New email registered: {email_request.email}")
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
async def get_stats(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Get basic statistics about email submissions (protected endpoint - requires admin authentication)"""
    global database_available
    
    if not database_available:
        return {
            "total_emails": "unavailable",
            "timestamp": datetime.utcnow(),
            "storage_type": "PostgreSQL Database",
            "database": "eindr_lp",
            "status": "database_unavailable"
        }
    
    try:
        logger.info(f"👤 Admin user '{current_user}' accessing stats endpoint")
        
        query = select(Email)
        result = await db.execute(query)
        emails = result.scalars().all()
        total_emails = len(emails)
        
        return {
            "total_emails": total_emails,
            "timestamp": datetime.utcnow(),
            "storage_type": "PostgreSQL Database",
            "database": "eindr_lp",
            "status": "connected",
            "accessed_by": current_user
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return {
            "total_emails": "error",
            "timestamp": datetime.utcnow(),
            "storage_type": "PostgreSQL Database",
            "database": "eindr_lp",
            "status": "error",
            "error": str(e)
        }


@app.get("/emails")
async def list_emails(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """List all stored emails (protected endpoint - requires admin authentication)"""
    global database_available
    
    if not database_available:
        raise HTTPException(
            status_code=503,
            detail="Database service is currently unavailable"
        )
    
    try:
        logger.info(f"👤 Admin user '{current_user}' accessing emails endpoint")
        
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
            "total": len(email_list),
            "accessed_by": current_user
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