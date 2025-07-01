from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.database_psycopg import Email, Language, LabelGroup, LabelCode, LanguageLabel
from app.models import (
    EmailSubmissionRequest, EmailSubmissionResponse,
    LanguageCreate, LanguageUpdate, Language as LanguageModel,
    LabelGroupCreate, LabelGroupUpdate, LabelGroup as LabelGroupModel,
    LabelCodeCreate, LabelCodeUpdate, LabelCode as LabelCodeModel,
    LanguageLabelCreate, LanguageLabelUpdate, LanguageLabel as LanguageLabelModel,
    LabelValidationRequest, LabelValidationResponse,
    LanguageLabelWithDetails, LabelsForLanguageResponse
)
import logging
from typing import List, Optional, Dict, Any

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


# ======== MULTI-LANGUAGE LABEL SYSTEM SERVICES ========

class LanguageService:
    """Service for managing languages"""
    
    @staticmethod
    async def create_language(language_data: LanguageCreate, db: AsyncSession) -> LanguageModel:
        """Create a new language"""
        try:
            language = Language(**language_data.dict())
            db.add(language)
            await db.commit()
            await db.refresh(language)
            logger.info(f"✅ Created new language: {language.name} ({language.code})")
            return LanguageModel.from_orm(language)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Language creation failed: {e}")
            raise ValueError(f"Language with name '{language_data.name}' or code '{language_data.code}' already exists")
    
    @staticmethod
    async def get_language(language_id: int, db: AsyncSession) -> Optional[LanguageModel]:
        """Get language by ID"""
        query = select(Language).where(Language.id == language_id)
        result = await db.execute(query)
        language = result.scalar_one_or_none()
        return LanguageModel.from_orm(language) if language else None
    
    @staticmethod
    async def get_all_languages(db: AsyncSession, active_only: bool = False) -> List[LanguageModel]:
        """Get all languages"""
        query = select(Language)
        if active_only:
            query = query.where(Language.active == True)
        query = query.order_by(Language.name)
        
        result = await db.execute(query)
        languages = result.scalars().all()
        return [LanguageModel.from_orm(lang) for lang in languages]
    
    @staticmethod
    async def update_language(language_id: int, language_data: LanguageUpdate, db: AsyncSession) -> Optional[LanguageModel]:
        """Update a language"""
        query = select(Language).where(Language.id == language_id)
        result = await db.execute(query)
        language = result.scalar_one_or_none()
        
        if not language:
            return None
        
        update_data = language_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(language, field, value)
        
        try:
            await db.commit()
            await db.refresh(language)
            logger.info(f"✅ Updated language: {language.name}")
            return LanguageModel.from_orm(language)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Language update failed: {e}")
            raise ValueError("Language name or code already exists")
    
    @staticmethod
    async def delete_language(language_id: int, db: AsyncSession) -> bool:
        """Delete a language (soft delete by setting is_active=False)"""
        query = select(Language).where(Language.id == language_id)
        result = await db.execute(query)
        language = result.scalar_one_or_none()
        
        if not language:
            return False
        
        language.active = False
        await db.commit()
        logger.info(f"✅ Deactivated language: {language.name}")
        return True


class LabelGroupService:
    """Service for managing label groups"""
    
    @staticmethod
    async def create_label_group(group_data: LabelGroupCreate, db: AsyncSession) -> LabelGroupModel:
        """Create a new label group"""
        try:
            group = LabelGroup(**group_data.dict())
            db.add(group)
            await db.commit()
            await db.refresh(group)
            logger.info(f"✅ Created new label group: {group.group_name}")
            return LabelGroupModel.from_orm(group)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Label group creation failed: {e}")
            raise ValueError(f"Label group with name '{group_data.group_name}' already exists")
    
    @staticmethod
    async def get_label_group(group_id: int, db: AsyncSession) -> Optional[LabelGroupModel]:
        """Get label group by ID"""
        query = select(LabelGroup).where(LabelGroup.id == group_id)
        result = await db.execute(query)
        group = result.scalar_one_or_none()
        return LabelGroupModel.from_orm(group) if group else None
    
    @staticmethod
    async def get_all_label_groups(db: AsyncSession) -> List[LabelGroupModel]:
        """Get all label groups"""
        query = select(LabelGroup).order_by(LabelGroup.group_name)
        result = await db.execute(query)
        groups = result.scalars().all()
        return [LabelGroupModel.from_orm(group) for group in groups]


class LabelCodeService:
    """Service for managing label codes"""
    
    @staticmethod
    async def create_label_code(code_data: LabelCodeCreate, db: AsyncSession) -> LabelCodeModel:
        """Create a new label code"""
        try:
            code = LabelCode(**code_data.dict())
            db.add(code)
            await db.commit()
            await db.refresh(code)
            logger.info(f"✅ Created new label code: {code.name}")
            return LabelCodeModel.from_orm(code)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Label code creation failed: {e}")
            raise ValueError(f"Label code '{code_data.name}' already exists in this group")
    
    @staticmethod
    async def get_label_code(code_id: int, db: AsyncSession) -> Optional[LabelCodeModel]:
        """Get label code by ID"""
        query = select(LabelCode).where(LabelCode.id == code_id)
        result = await db.execute(query)
        code = result.scalar_one_or_none()
        return LabelCodeModel.from_orm(code) if code else None
    
    @staticmethod
    async def get_label_codes_by_group(group_id: int, db: AsyncSession) -> List[LabelCodeModel]:
        """Get all label codes for a specific group"""
        query = select(LabelCode).where(LabelCode.label_group_id == group_id).order_by(LabelCode.name)
        result = await db.execute(query)
        codes = result.scalars().all()
        return [LabelCodeModel.from_orm(code) for code in codes]


class LanguageLabelService:
    """Service for managing language labels (translations)"""
    
    @staticmethod
    async def validate_label_data(validation_request: LabelValidationRequest, db: AsyncSession) -> LabelValidationResponse:
        """Validate language, label group, and label code existence before insertion"""
        
        # Check if language exists
        language_query = select(Language).where(Language.id == validation_request.language_id)
        language_result = await db.execute(language_query)
        language_exists = language_result.scalar_one_or_none() is not None
        
        # Check if label group exists
        group_query = select(LabelGroup).where(LabelGroup.id == validation_request.label_group_id)
        group_result = await db.execute(group_query)
        label_group_exists = group_result.scalar_one_or_none() is not None
        
        # Check if label code exists and belongs to the specified group
        code_query = select(LabelCode).where(
            and_(
                LabelCode.id == validation_request.label_code_id,
                LabelCode.label_group_id == validation_request.label_group_id
            )
        )
        code_result = await db.execute(code_query)
        label_code_exists = code_result.scalar_one_or_none() is not None
        
        valid = language_exists and label_group_exists and label_code_exists
        
        if valid:
            message = "✅ All validation checks passed. Ready to insert label."
        else:
            errors = []
            if not language_exists:
                errors.append("Language not found")
            if not label_group_exists:
                errors.append("Label group not found")
            if not label_code_exists:
                errors.append("Label code not found or doesn't belong to the specified group")
            message = f"❌ Validation failed: {', '.join(errors)}"
        
        return LabelValidationResponse(
            valid=valid,
            language_exists=language_exists,
            label_group_exists=label_group_exists,
            label_code_exists=label_code_exists,
            message=message
        )
    
    @staticmethod
    async def create_language_label(label_data: LanguageLabelCreate, db: AsyncSession) -> LanguageLabelModel:
        """Create a new language label (translation)"""
        try:
            # First validate the data
            validation_request = LabelValidationRequest(
                language_id=label_data.language_id,
                label_group_id=0,  # We'll get this from the label code
                label_code_id=label_data.label_id,
                label_text=label_data.label_text
            )
            
            # Get the label code to find its group
            code_query = select(LabelCode).where(LabelCode.id == label_data.label_id)
            code_result = await db.execute(code_query)
            label_code = code_result.scalar_one_or_none()
            
            if not label_code:
                raise ValueError("Label code not found")
            
            validation_request.label_group_id = label_code.label_group_id
            validation_result = await LanguageLabelService.validate_label_data(validation_request, db)
            
            if not validation_result.valid:
                raise ValueError(validation_result.message)
            
            # Create the language label
            language_label = LanguageLabel(**label_data.dict())
            db.add(language_label)
            await db.commit()
            await db.refresh(language_label)
            
            logger.info(f"✅ Created language label: Language {label_data.language_id}, Label {label_data.label_id}")
            return LanguageLabelModel.from_orm(language_label)
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Language label creation failed: {e}")
            raise ValueError("Language label already exists for this language and label code")
    
    @staticmethod
    async def get_language_label(language_id: int, label_id: int, db: AsyncSession) -> Optional[LanguageLabelModel]:
        """Get a specific language label"""
        query = select(LanguageLabel).where(
            and_(
                LanguageLabel.language_id == language_id,
                LanguageLabel.label_id == label_id
            )
        )
        result = await db.execute(query)
        label = result.scalar_one_or_none()
        return LanguageLabelModel.from_orm(label) if label else None
    
    @staticmethod
    async def get_labels_for_language(language_id: int, db: AsyncSession) -> LabelsForLanguageResponse:
        """Get all labels for a specific language, grouped by label groups"""
        
        # Get language info
        language_query = select(Language).where(Language.id == language_id)
        language_result = await db.execute(language_query)
        language = language_result.scalar_one_or_none()
        
        if not language:
            raise ValueError("Language not found")
        
        # Get all language labels with related data
        query = select(LanguageLabel, LabelCode, LabelGroup).join(
            LabelCode, LanguageLabel.label_id == LabelCode.id
        ).join(
            LabelGroup, LabelCode.label_group_id == LabelGroup.id
        ).where(LanguageLabel.language_id == language_id).order_by(
            LabelGroup.group_name, LabelCode.name
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Group labels by label group
        labels_by_group = {}
        total_labels = 0
        
        for language_label, label_code, label_group in rows:
            group_name = label_group.group_name
            if group_name not in labels_by_group:
                labels_by_group[group_name] = {}
            
            labels_by_group[group_name][label_code.name] = language_label.label_text
            total_labels += 1
        
        return LabelsForLanguageResponse(
            language_id=language.id,
            language_name=language.name,
            language_code=language.lang_code,
            labels=labels_by_group,
            total_labels=total_labels
        )
    
    @staticmethod
    async def update_language_label(
        language_id: int, 
        label_id: int, 
        label_data: LanguageLabelUpdate, 
        db: AsyncSession
    ) -> Optional[LanguageLabelModel]:
        """Update a language label"""
        query = select(LanguageLabel).where(
            and_(
                LanguageLabel.language_id == language_id,
                LanguageLabel.label_id == label_id
            )
        )
        result = await db.execute(query)
        language_label = result.scalar_one_or_none()
        
        if not language_label:
            return None
        
        update_data = label_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(language_label, field, value)
        
        await db.commit()
        await db.refresh(language_label)
        logger.info(f"✅ Updated language label: Language {language_id}, Label {label_id}")
        return LanguageLabelModel.from_orm(language_label)
    
    @staticmethod
    async def delete_language_label(language_id: int, label_id: int, db: AsyncSession) -> bool:
        """Delete a language label"""
        query = select(LanguageLabel).where(
            and_(
                LanguageLabel.language_id == language_id,
                LanguageLabel.label_id == label_id
            )
        )
        result = await db.execute(query)
        language_label = result.scalar_one_or_none()
        
        if not language_label:
            return False
        
        await db.delete(language_label)
        await db.commit()
        logger.info(f"✅ Deleted language label: Language {language_id}, Label {label_id}")
        return True
    
    @staticmethod
    async def get_language_labels_with_details(db: AsyncSession, language_id: Optional[int] = None) -> List[LanguageLabelWithDetails]:
        """Get language labels with detailed information"""
        query = select(
            LanguageLabel,
            Language,
            LabelCode,
            LabelGroup
        ).join(
            Language, LanguageLabel.language_id == Language.id
        ).join(
            LabelCode, LanguageLabel.label_id == LabelCode.id
        ).join(
            LabelGroup, LabelCode.label_group_id == LabelGroup.id
        )
        
        if language_id:
            query = query.where(LanguageLabel.language_id == language_id)
        
        query = query.order_by(Language.name, LabelGroup.group_name, LabelCode.name)
        
        result = await db.execute(query)
        rows = result.all()
        
        details = []
        for language_label, language, label_code, label_group in rows:
            details.append(LanguageLabelWithDetails(
                id=language_label.id,
                language_id=language.id,
                language_name=language.name,
                language_code=language.lang_code,
                label_id=label_code.id,
                label_code=label_code.name,
                label_group_name=label_group.group_name,
                label_text=language_label.label_text
            ))
        
        return details 