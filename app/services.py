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
    LanguageLabelWithDetails, LabelsForLanguageResponse,
    BulkLabelRequest, BulkLabelResponse, BulkLabelResult, BulkLabelItem
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
    
    @staticmethod
    async def update_label_group(group_id: int, group_data: LabelGroupUpdate, db: AsyncSession) -> Optional[LabelGroupModel]:
        """Update a label group"""
        query = select(LabelGroup).where(LabelGroup.id == group_id)
        result = await db.execute(query)
        group = result.scalar_one_or_none()
        
        if not group:
            return None
        
        update_data = group_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)
        
        try:
            await db.commit()
            await db.refresh(group)
            logger.info(f"✅ Updated label group: {group.group_name}")
            return LabelGroupModel.from_orm(group)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Label group update failed: {e}")
            raise ValueError("Label group name already exists")
    
    @staticmethod
    async def delete_label_group(group_id: int, db: AsyncSession) -> bool:
        """Delete a label group"""
        query = select(LabelGroup).where(LabelGroup.id == group_id)
        result = await db.execute(query)
        group = result.scalar_one_or_none()
        
        if not group:
            return False
        
        await db.delete(group)
        await db.commit()
        logger.info(f"✅ Deleted label group: {group.group_name}")
        return True


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
            raise ValueError(f"Label code with name '{code_data.name}' already exists in this group")
    
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
    
    @staticmethod
    async def get_label_code_by_name_and_group(name: str, group_id: int, db: AsyncSession) -> Optional[LabelCode]:
        """Get label code by name and group ID"""
        query = select(LabelCode).where(
            and_(LabelCode.name == name, LabelCode.label_group_id == group_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


class LanguageLabelService:
    """Service for managing language labels"""
    
    @staticmethod
    async def validate_label_data(validation_request: LabelValidationRequest, db: AsyncSession) -> LabelValidationResponse:
        """Validate language, label group, and label code existence"""
        try:
            # Check if language exists
            language_query = select(Language).where(Language.id == validation_request.language_id)
            language_result = await db.execute(language_query)
            language_exists = language_result.scalar_one_or_none() is not None
            
            # Check if label group exists
            group_query = select(LabelGroup).where(LabelGroup.id == validation_request.label_group_id)
            group_result = await db.execute(group_query)
            group_exists = group_result.scalar_one_or_none() is not None
            
            # Check if label code exists and belongs to the group
            code_query = select(LabelCode).where(
                and_(
                    LabelCode.id == validation_request.label_code_id,
                    LabelCode.label_group_id == validation_request.label_group_id
                )
            )
            code_result = await db.execute(code_query)
            code_exists = code_result.scalar_one_or_none() is not None
            
            # Check if translation already exists
            existing_translation_query = select(LanguageLabel).where(
                and_(
                    LanguageLabel.language_id == validation_request.language_id,
                    LanguageLabel.label_id == validation_request.label_code_id
                )
            )
            existing_result = await db.execute(existing_translation_query)
            translation_exists = existing_result.scalar_one_or_none() is not None
            
            # Determine if data is valid
            valid = language_exists and group_exists and code_exists and not translation_exists
            
            # Generate appropriate message
            if not language_exists:
                message = f"Language with ID {validation_request.language_id} does not exist"
            elif not group_exists:
                message = f"Label group with ID {validation_request.label_group_id} does not exist"
            elif not code_exists:
                message = f"Label code with ID {validation_request.label_code_id} does not exist or does not belong to the specified group"
            elif translation_exists:
                message = f"Translation for language {validation_request.language_id} and label code {validation_request.label_code_id} already exists"
            else:
                message = "✅ All validation checks passed - ready for insertion"
            
            return LabelValidationResponse(
                valid=valid,
                language_exists=language_exists,
                label_group_exists=group_exists,
                label_code_exists=code_exists,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error validating label data: {e}")
            return LabelValidationResponse(
                valid=False,
                language_exists=False,
                label_group_exists=False,
                label_code_exists=False,
                message=f"Validation error: {str(e)}"
            )
    
    @staticmethod
    async def create_language_label(label_data: LanguageLabelCreate, db: AsyncSession) -> LanguageLabelModel:
        """Create a new language label"""
        try:
            # Check if translation already exists
            existing_query = select(LanguageLabel).where(
                and_(
                    LanguageLabel.language_id == label_data.language_id,
                    LanguageLabel.label_id == label_data.label_id
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                raise ValueError(f"Translation for language {label_data.language_id} and label {label_data.label_id} already exists")
            
            # Create new translation
            language_label = LanguageLabel(**label_data.dict())
            db.add(language_label)
            await db.commit()
            await db.refresh(language_label)
            
            logger.info(f"✅ Created new language label: language_id={label_data.language_id}, label_id={label_data.label_id}")
            return LanguageLabelModel.from_orm(language_label)
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"❌ Language label creation failed: {e}")
            raise ValueError("Translation already exists or invalid data")
    
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
        """Get all labels for a specific language, organized by label groups"""
        try:
            # Get language info
            language_query = select(Language).where(Language.id == language_id)
            language_result = await db.execute(language_query)
            language = language_result.scalar_one_or_none()
            
            if not language:
                raise ValueError(f"Language with ID {language_id} not found")
            
            # Get all labels for this language with related data
            query = select(LanguageLabel, LabelCode, LabelGroup).join(
                LabelCode, LanguageLabel.label_id == LabelCode.id
            ).join(
                LabelGroup, LabelCode.label_group_id == LabelGroup.id
            ).where(LanguageLabel.language_id == language_id)
            
            result = await db.execute(query)
            rows = result.all()
            
            # Organize labels by group
            labels_by_group = {}
            total_labels = 0
            
            for row in rows:
                language_label, label_code, label_group = row
                
                if label_group.group_name not in labels_by_group:
                    labels_by_group[label_group.group_name] = {}
                
                labels_by_group[label_group.group_name][label_code.name] = language_label.label_text
                total_labels += 1
            
            return LabelsForLanguageResponse(
                language_id=language_id,
                language_name=language.name,
                language_code=language.lang_code,
                labels=labels_by_group,
                total_labels=total_labels
            )
            
        except Exception as e:
            logger.error(f"Error fetching labels for language {language_id}: {e}")
            raise
    
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
        
        try:
            await db.commit()
            await db.refresh(language_label)
            logger.info(f"✅ Updated language label: language_id={language_id}, label_id={label_id}")
            return LanguageLabelModel.from_orm(language_label)
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Language label update failed: {e}")
            raise ValueError("Failed to update language label")
    
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
        logger.info(f"✅ Deleted language label: language_id={language_id}, label_id={label_id}")
        return True
    
    @staticmethod
    async def get_language_labels_with_details(db: AsyncSession, language_id: Optional[int] = None) -> List[LanguageLabelWithDetails]:
        """Get language labels with detailed information"""
        query = select(
            LanguageLabel, Language, LabelCode, LabelGroup
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
        
        return [
            LanguageLabelWithDetails(
                id=row[0].id,
                language_id=row[0].language_id,
                language_name=row[1].name,
                language_code=row[1].lang_code,
                label_id=row[0].label_id,
                label_code=row[2].name,
                label_group_name=row[3].group_name,
                label_text=row[0].label_text
            )
            for row in rows
        ]


# ======== BULK OPERATIONS SERVICE ========

class BulkLabelService:
    """Service for bulk label operations"""
    
    @staticmethod
    async def bulk_insert_labels(bulk_request: BulkLabelRequest, db: AsyncSession) -> BulkLabelResponse:
        """
        Insert multiple labels in bulk for a specific language and label group
        
        Args:
            bulk_request: Bulk label insertion request with optional update support
            db: Database session
            
        Returns:
            BulkLabelResponse with detailed results including insertions, updates, and skips
        """
        logger.info(f"🚀 Starting bulk label operation: {len(bulk_request.labels)} labels for language {bulk_request.language_id}, group {bulk_request.label_group_id}, allow_updates={bulk_request.allow_updates}")
        
        results = []
        successful_insertions = 0
        successful_updates = 0
        failed_insertions = 0
        skipped_labels = 0
        
        # Validate language and group existence first
        language_query = select(Language).where(Language.id == bulk_request.language_id)
        language_result = await db.execute(language_query)
        language = language_result.scalar_one_or_none()
        
        if not language:
            return BulkLabelResponse(
                success=False,
                total_labels=len(bulk_request.labels),
                successful_insertions=0,
                successful_updates=0,
                failed_insertions=len(bulk_request.labels),
                skipped_labels=0,
                results=[],
                message=f"Language with ID {bulk_request.language_id} does not exist"
            )
        
        group_query = select(LabelGroup).where(LabelGroup.id == bulk_request.label_group_id)
        group_result = await db.execute(group_query)
        group = group_result.scalar_one_or_none()
        
        if not group:
            return BulkLabelResponse(
                success=False,
                total_labels=len(bulk_request.labels),
                successful_insertions=0,
                successful_updates=0,
                failed_insertions=len(bulk_request.labels),
                skipped_labels=0,
                results=[],
                message=f"Label group with ID {bulk_request.label_group_id} does not exist"
            )
        
        # Process each label
        for label_item in bulk_request.labels:
            try:
                # Get or create label code
                label_code = await LabelCodeService.get_label_code_by_name_and_group(
                    label_item.label_code_name, 
                    bulk_request.label_group_id, 
                    db
                )
                
                if not label_code:
                    # Create the label code if it doesn't exist
                    label_code_data = LabelCodeCreate(
                        name=label_item.label_code_name,
                        label_group_id=bulk_request.label_group_id
                    )
                    label_code = await LabelCodeService.create_label_code(label_code_data, db)
                    logger.info(f"✅ Created new label code: {label_item.label_code_name}")
                
                # Check if translation already exists (fetch ORM object directly)
                existing_query = select(LanguageLabel).where(
                    and_(
                        LanguageLabel.language_id == bulk_request.language_id,
                        LanguageLabel.label_id == label_code.id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_label_obj = existing_result.scalar_one_or_none()

                if existing_label_obj:
                    if bulk_request.allow_updates:
                        # Compare the actual DB value
                        if existing_label_obj.label_text == label_item.label_text:
                            # No change, skip
                            results.append(BulkLabelResult(
                                label_code_name=label_item.label_code_name,
                                label_text=label_item.label_text,
                                success=False,
                                message=f"Translation already exists with same text for label code '{label_item.label_code_name}'",
                                label_id=existing_label_obj.id,
                                action="skipped"
                            ))
                            skipped_labels += 1
                            logger.info(f"⏭️  Skipped unchanged label: {label_item.label_code_name}")
                        else:
                            # Text has changed, update it
                            try:
                                old_text = existing_label_obj.label_text
                                existing_label_obj.label_text = label_item.label_text
                                await db.commit()
                                await db.refresh(existing_label_obj)
                                results.append(BulkLabelResult(
                                    label_code_name=label_item.label_code_name,
                                    label_text=label_item.label_text,
                                    success=True,
                                    message=f"Successfully updated existing translation (changed from '{old_text}' to '{label_item.label_text}')",
                                    label_id=existing_label_obj.id,
                                    action="updated"
                                ))
                                successful_updates += 1
                                logger.info(f"✅ Successfully updated label: {label_item.label_code_name}")
                            except Exception as update_error:
                                await db.rollback()
                                logger.error(f"❌ Failed to update label {label_item.label_code_name}: {update_error}")
                                results.append(BulkLabelResult(
                                    label_code_name=label_item.label_code_name,
                                    label_text=label_item.label_text,
                                    success=False,
                                    message=f"Update error: {str(update_error)}",
                                    label_id=existing_label_obj.id,
                                    action="failed_update"
                                ))
                                failed_insertions += 1
                    else:
                        # Skip existing translation (no updates allowed)
                        results.append(BulkLabelResult(
                            label_code_name=label_item.label_code_name,
                            label_text=label_item.label_text,
                            success=False,
                            message=f"Translation already exists for label code '{label_item.label_code_name}' (use allow_updates=true to update)",
                            label_id=existing_label_obj.id,
                            action="skipped"
                        ))
                        skipped_labels += 1
                        logger.info(f"⏭️  Skipped existing label: {label_item.label_code_name}")
                    continue
                
                # Create new translation
                label_data = LanguageLabelCreate(
                    language_id=bulk_request.language_id,
                    label_id=label_code.id,
                    label_text=label_item.label_text
                )
                
                created_label = await LanguageLabelService.create_language_label(label_data, db)
                
                results.append(BulkLabelResult(
                    label_code_name=label_item.label_code_name,
                    label_text=label_item.label_text,
                    success=True,
                    message="Successfully inserted new translation",
                    label_id=created_label.id,
                    action="inserted"
                ))
                successful_insertions += 1
                
                logger.info(f"✅ Successfully inserted label: {label_item.label_code_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process label {label_item.label_code_name}: {e}")
                results.append(BulkLabelResult(
                    label_code_name=label_item.label_code_name,
                    label_text=label_item.label_text,
                    success=False,
                    message=f"Error: {str(e)}",
                    action="failed"
                ))
                failed_insertions += 1
        
        # Determine overall success
        total_successful = successful_insertions + successful_updates
        overall_success = failed_insertions == 0
        
        # Generate message
        if overall_success and total_successful == len(bulk_request.labels):
            message = f"✅ Successfully processed all {len(bulk_request.labels)} labels"
        elif total_successful > 0:
            message = f"⚠️  Partially successful: {successful_insertions} inserted, {successful_updates} updated, {skipped_labels} skipped, {failed_insertions} failed"
        else:
            message = f"❌ Failed to process any labels: {failed_insertions} errors"
        
        # Add detailed breakdown
        details = []
        if successful_insertions > 0:
            details.append(f"{successful_insertions} new")
        if successful_updates > 0:
            details.append(f"{successful_updates} updated")
        if skipped_labels > 0:
            details.append(f"{skipped_labels} already exist")
        if failed_insertions > 0:
            details.append(f"{failed_insertions} failed")
        
        if details:
            message += f" ({', '.join(details)})"
        
        logger.info(f"🏁 Bulk operation completed: {successful_insertions} inserted, {successful_updates} updated, {skipped_labels} skipped, {failed_insertions} failed")
        
        return BulkLabelResponse(
            success=overall_success,
            total_labels=len(bulk_request.labels),
            successful_insertions=successful_insertions,
            successful_updates=successful_updates,
            failed_insertions=failed_insertions,
            skipped_labels=skipped_labels,
            results=results,
            message=message
        ) 