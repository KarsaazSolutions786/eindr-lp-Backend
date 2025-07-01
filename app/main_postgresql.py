from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os
import secrets
from typing import List, Optional

from app.database_psycopg import get_database_session, create_tables, close_database, Email
from app.models import (
    EmailSubmissionRequest, EmailSubmissionResponse, HealthCheckResponse,
    # Multi-language label system models
    LanguageCreate, LanguageUpdate, Language,
    LabelGroupCreate, LabelGroupUpdate, LabelGroup,
    LabelCodeCreate, LabelCodeUpdate, LabelCode,
    LanguageLabelCreate, LanguageLabelUpdate, LanguageLabel,
    LabelValidationRequest, LabelValidationResponse,
    LanguageLabelWithDetails, LabelsForLanguageResponse
)
from app.services import (
    EmailService,
    LanguageService, LabelGroupService, LabelCodeService, LanguageLabelService
)

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
    logger.info("🚀 Starting Eindr Email Capture API with PostgreSQL + Multi-Language Label System...")
    
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
    title="Eindr Email Capture + Multi-Language Label Management API",
    description="Backend API for capturing email addresses and managing multi-language labels",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In development, allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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


# ======== ORIGINAL EMAIL CAPTURE ENDPOINTS ========

@app.get("/")
async def root():
    """Root endpoint serving the index page"""
    return FileResponse("app/templates/index.html")


@app.get("/api/health", response_model=HealthCheckResponse)
async def root_health():
    """Root endpoint for health check (JSON response)"""
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


@app.get("/admin")
async def admin_panel():
    """Serve the admin panel for managing labels"""
    return FileResponse("app/templates/admin_panel.html")


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


# ======== MULTI-LANGUAGE LABEL MANAGEMENT ENDPOINTS ========

# === LANGUAGE ENDPOINTS ===

@app.post("/api/languages", response_model=Language)
async def create_language(
    language_data: LanguageCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Create a new language (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' creating language: {language_data.name}")
        return await LanguageService.create_language(language_data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating language: {e}")
        raise HTTPException(status_code=500, detail="Failed to create language")


@app.get("/api/languages", response_model=List[Language])
async def get_languages(
    active_only: bool = False,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all languages (public endpoint)"""
    try:
        return await LanguageService.get_all_languages(db, active_only=active_only)
    except Exception as e:
        logger.error(f"Error fetching languages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch languages")


@app.get("/api/languages/{language_id}", response_model=Language)
async def get_language(
    language_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get a specific language by ID (public endpoint)"""
    language = await LanguageService.get_language(language_id, db)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    return language


@app.put("/api/languages/{language_id}", response_model=Language)
async def update_language(
    language_id: int,
    language_data: LanguageUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Update a language (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' updating language ID: {language_id}")
        updated_language = await LanguageService.update_language(language_id, language_data, db)
        if not updated_language:
            raise HTTPException(status_code=404, detail="Language not found")
        return updated_language
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating language: {e}")
        raise HTTPException(status_code=500, detail="Failed to update language")


@app.delete("/api/languages/{language_id}")
async def delete_language(
    language_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Deactivate a language (Admin only)"""
    logger.info(f"👤 Admin '{current_user}' deactivating language ID: {language_id}")
    success = await LanguageService.delete_language(language_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Language not found")
    return {"message": "Language deactivated successfully"}


# === LABEL GROUP ENDPOINTS ===

@app.post("/api/label-groups", response_model=LabelGroup)
async def create_label_group(
    group_data: LabelGroupCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Create a new label group (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' creating label group: {group_data.name}")
        return await LabelGroupService.create_label_group(group_data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating label group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create label group")


@app.get("/api/label-groups")
async def get_label_groups():
    """Get all label groups (public endpoint)"""
    try:
        async for db in get_database_session():
            # Use raw SQL query since the service works
            from sqlalchemy import text
            result = await db.execute(text("SELECT id, group_name FROM label_groups ORDER BY group_name"))
            rows = result.fetchall()
            
            # Convert to simple dict format
            groups = []
            for row in rows:
                groups.append({
                    "id": row[0],
                    "group_name": row[1]
                })
            
            return groups
            
    except Exception as e:
        logger.error(f"Error fetching label groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch label groups")


@app.get("/api/label-groups/{group_id}")
async def get_label_group(group_id: int):
    """Get a specific label group by ID (public endpoint)"""
    try:
        async for db in get_database_session():
            # Use raw SQL query for consistency
            from sqlalchemy import text
            result = await db.execute(text("SELECT id, group_name FROM label_groups WHERE id = :group_id"), {"group_id": group_id})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Label group not found")
            
            return {
                "id": row[0],
                "group_name": row[1]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching label group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch label group")


# === LABEL CODE ENDPOINTS ===

@app.post("/api/label-codes", response_model=LabelCode)
async def create_label_code(
    code_data: LabelCodeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Create a new label code (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' creating label code: {code_data.name}")
        return await LabelCodeService.create_label_code(code_data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating label code: {e}")
        raise HTTPException(status_code=500, detail="Failed to create label code")


@app.get("/api/label-codes/{code_id}", response_model=LabelCode)
async def get_label_code(
    code_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get a specific label code by ID (public endpoint)"""
    code = await LabelCodeService.get_label_code(code_id, db)
    if not code:
        raise HTTPException(status_code=404, detail="Label code not found")
    return code


@app.get("/api/label-groups/{group_id}/codes", response_model=List[LabelCode])
async def get_label_codes_by_group(
    group_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all label codes for a specific group (public endpoint)"""
    try:
        return await LabelCodeService.get_label_codes_by_group(group_id, db)
    except Exception as e:
        logger.error(f"Error fetching label codes for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch label codes")


# === LANGUAGE LABEL ENDPOINTS (Core Translation Management) ===

@app.post("/api/labels/validate", response_model=LabelValidationResponse)
async def validate_label_data(
    validation_request: LabelValidationRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """
    Validate language, label group, and label code existence before insertion
    This endpoint implements Step 1 of your SQL validation process
    """
    try:
        logger.info(f"👤 Admin '{current_user}' validating label data")
        return await LanguageLabelService.validate_label_data(validation_request, db)
    except Exception as e:
        logger.error(f"Error validating label data: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate label data")


@app.post("/api/language-labels", response_model=LanguageLabel)
async def create_language_label(
    label_data: LanguageLabelCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """
    Create a new language label (translation)
    This endpoint implements Step 2 of your SQL process - the INSERT operation
    """
    try:
        logger.info(f"👤 Admin '{current_user}' creating language label")
        return await LanguageLabelService.create_language_label(label_data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating language label: {e}")
        raise HTTPException(status_code=500, detail="Failed to create language label")


@app.get("/api/language-labels/{language_id}/{label_id}", response_model=LanguageLabel)
async def get_language_label(
    language_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get a specific language label
    This endpoint implements Step 3 of your SQL process - the verification SELECT
    """
    label = await LanguageLabelService.get_language_label(language_id, label_id, db)
    if not label:
        raise HTTPException(status_code=404, detail="Language label not found")
    return label


@app.put("/api/language-labels/{language_id}/{label_id}", response_model=LanguageLabel)
async def update_language_label(
    language_id: int,
    label_id: int,
    label_data: LanguageLabelUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Update a language label (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' updating language label")
        updated_label = await LanguageLabelService.update_language_label(
            language_id, label_id, label_data, db
        )
        if not updated_label:
            raise HTTPException(status_code=404, detail="Language label not found")
        return updated_label
    except Exception as e:
        logger.error(f"Error updating language label: {e}")
        raise HTTPException(status_code=500, detail="Failed to update language label")


@app.delete("/api/language-labels/{language_id}/{label_id}")
async def delete_language_label(
    language_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Delete a language label (Admin only)"""
    logger.info(f"👤 Admin '{current_user}' deleting language label")
    success = await LanguageLabelService.delete_language_label(language_id, label_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Language label not found")
    return {"message": "Language label deleted successfully"}


# === COMPREHENSIVE QUERY ENDPOINTS ===

@app.get("/api/languages/{language_id}/labels", response_model=LabelsForLanguageResponse)
async def get_labels_for_language(
    language_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all labels for a specific language, organized by label groups (public endpoint)"""
    try:
        return await LanguageLabelService.get_labels_for_language(language_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching labels for language {language_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch labels for language")


@app.get("/api/language-labels", response_model=List[LanguageLabelWithDetails])
async def get_language_labels_with_details(
    language_id: Optional[int] = None,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """Get language labels with detailed information (Admin only)"""
    try:
        logger.info(f"👤 Admin '{current_user}' fetching detailed language labels")
        return await LanguageLabelService.get_language_labels_with_details(db, language_id)
    except Exception as e:
        logger.error(f"Error fetching detailed language labels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch detailed language labels")


# === COMBINED ENDPOINT FOR STEP-BY-STEP LABEL INSERTION ===

@app.post("/api/labels/insert-with-validation")
async def insert_label_with_validation(
    validation_request: LabelValidationRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(authenticate_admin)
):
    """
    Complete label insertion workflow with validation
    This combines all 3 steps from your SQL process:
    1. Validate existence of language, label group, and label code
    2. Insert the language label
    3. Return the verification result
    """
    try:
        logger.info(f"👤 Admin '{current_user}' performing complete label insertion workflow")
        
        # Step 1: Validate
        validation_result = await LanguageLabelService.validate_label_data(validation_request, db)
        
        if not validation_result.valid:
            return {
                "step": "validation",
                "success": False,
                "validation_result": validation_result,
                "message": validation_result.message
            }
        
        # Step 2: Insert
        label_data = LanguageLabelCreate(
            language_id=validation_request.language_id,
            label_id=validation_request.label_code_id,
            label_text=validation_request.label_text
        )
        
        try:
            created_label = await LanguageLabelService.create_language_label(label_data, db)
        except ValueError as e:
            return {
                "step": "insertion",
                "success": False,
                "validation_result": validation_result,
                "message": f"Insertion failed: {str(e)}"
            }
        
        # Step 3: Verify
        verification_result = await LanguageLabelService.get_language_label(
            validation_request.language_id, 
            validation_request.label_code_id, 
            db
        )
        
        return {
            "step": "complete",
            "success": True,
            "validation_result": validation_result,
            "created_label": created_label,
            "verification_result": verification_result,
            "message": "✅ Label successfully validated, inserted, and verified!"
        }
        
    except Exception as e:
        logger.error(f"Error in complete label insertion workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete label insertion workflow")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(
        "app.main_postgresql:app",
        host="0.0.0.0",
        port=port,
        reload=True
    ) 