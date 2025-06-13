from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import Email
from app.models import EmailSubmissionRequest, EmailSubmissionResponse
import logging

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    async def submit_email(
        email_request: EmailSubmissionRequest, 
        db: AsyncSession
    ) -> EmailSubmissionResponse:
        """
        Submit an email to the database
        
        Args:
            email_request: The email submission request
            db: Database session
            
        Returns:
            EmailSubmissionResponse with success status and message
        """
        try:
            # Check if email already exists
            existing_email = await EmailService.get_email_by_address(
                email_request.email, db
            )
            
            if existing_email:
                logger.info(f"Email already exists: {email_request.email}")
                return EmailSubmissionResponse(
                    success=True,
                    message="Email already registered. Thank you for your interest!",
                    email_id=existing_email.id
                )
            
            # Create new email record
            new_email = Email(email=email_request.email)
            db.add(new_email)
            await db.commit()
            await db.refresh(new_email)
            
            logger.info(f"New email submitted: {email_request.email}")
            return EmailSubmissionResponse(
                success=True,
                message="Email successfully registered. We'll keep you updated!",
                email_id=new_email.id
            )
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Database integrity error: {e}")
            return EmailSubmissionResponse(
                success=False,
                message="Email already registered. Thank you for your interest!"
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error submitting email: {e}")
            return EmailSubmissionResponse(
                success=False,
                message="An error occurred. Please try again later."
            )
    
    @staticmethod
    async def get_email_by_address(email_address: str, db: AsyncSession) -> Email:
        """Get email record by email address"""
        query = select(Email).where(Email.email == email_address.lower().strip())
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_email_count(db: AsyncSession) -> int:
        """Get total count of registered emails"""
        query = select(Email)
        result = await db.execute(query)
        return len(result.scalars().all()) 