from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List


class EmailSubmissionRequest(BaseModel):
    """Request model for email submission"""
    email: EmailStr = Field(..., description="Valid email address to register")
    
    @validator("email")
    def validate_email_format(cls, v):
        # Additional email validation if needed
        email_str = str(v).lower().strip()
        if len(email_str) > 255:
            raise ValueError("Email address is too long")
        return email_str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class EmailSubmissionResponse(BaseModel):
    """Response model for email submission"""
    success: bool = Field(..., description="Whether the submission was successful")
    message: str = Field(..., description="Human-readable response message")
    email_id: Optional[str] = Field(None, description="Unique identifier for the email record")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email successfully registered. We'll keep you updated!",
                "email_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class EmailRecord(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    version: str = Field(default="1.0.0", description="API version")
    database_status: Optional[str] = Field(None, description="Database connection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-12-01T12:00:00Z",
                "version": "1.0.0",
                "database_status": "connected"
            }
        }


# ======== MULTI-LANGUAGE LABEL SYSTEM MODELS ========

class LanguageBase(BaseModel):
    """Base model for Language"""
    name: str = Field(..., description="Language name (e.g., 'English', 'Spanish')")
    lang_code: str = Field(..., description="ISO language code (e.g., 'en', 'es')")
    direction: str = Field(..., description="Text direction (e.g., 'left', 'right')")
    active: bool = Field(default=True, description="Whether the language is active")
    icon: Optional[str] = Field(None, description="Icon for the language")


class LanguageCreate(LanguageBase):
    """Model for creating a new language"""
    pass


class LanguageUpdate(BaseModel):
    """Model for updating a language"""
    name: Optional[str] = None
    lang_code: Optional[str] = None
    direction: Optional[str] = None
    active: Optional[bool] = None
    icon: Optional[str] = None


class Language(LanguageBase):
    """Model for Language response"""
    id: int
    
    class Config:
        from_attributes = True


class LabelGroupBase(BaseModel):
    """Base model for Label Group"""
    group_name: str = Field(..., description="Group name (e.g., 'home', 'navigation')")


class LabelGroupCreate(LabelGroupBase):
    """Model for creating a new label group"""
    pass


class LabelGroupUpdate(BaseModel):
    """Model for updating a label group"""
    group_name: Optional[str] = None


class LabelGroup(LabelGroupBase):
    """Model for Label Group response"""
    id: int
    
    class Config:
        from_attributes = True


class LabelCodeBase(BaseModel):
    """Base model for Label Code"""
    name: str = Field(..., description="Label code name (e.g., 'text_home', 'btn_submit')")
    label_group_id: Optional[int] = Field(None, description="ID of the parent label group")


class LabelCodeCreate(LabelCodeBase):
    """Model for creating a new label code"""
    pass


class LabelCodeUpdate(BaseModel):
    """Model for updating a label code"""
    name: Optional[str] = None
    label_group_id: Optional[int] = None


class LabelCode(LabelCodeBase):
    """Model for Label Code response"""
    id: int
    
    class Config:
        from_attributes = True


class LanguageLabelBase(BaseModel):
    """Base model for Language Label"""
    language_id: int = Field(..., description="ID of the language")
    label_id: int = Field(..., description="ID of the label code")
    label_text: str = Field(..., description="Translated text for this label")


class LanguageLabelCreate(LanguageLabelBase):
    """Model for creating a new language label"""
    pass


class LanguageLabelUpdate(BaseModel):
    """Model for updating a language label"""
    label_text: Optional[str] = None


class LanguageLabel(LanguageLabelBase):
    """Model for Language Label response"""
    id: int
    
    class Config:
        from_attributes = True


class LanguageLabelWithDetails(BaseModel):
    """Model for Language Label with related details"""
    id: int
    language_id: int
    language_name: str
    language_code: str
    label_id: int
    label_code: str
    label_group_name: str
    label_text: str
    
    class Config:
        from_attributes = True


class LabelValidationRequest(BaseModel):
    """Model for validating label insertion data"""
    language_id: int = Field(..., description="ID of the language")
    label_group_id: int = Field(..., description="ID of the label group")
    label_code_id: int = Field(..., description="ID of the label code")
    label_text: str = Field(..., description="Text to be inserted")


class LabelValidationResponse(BaseModel):
    """Model for label validation response"""
    valid: bool = Field(..., description="Whether the data is valid for insertion")
    language_exists: bool = Field(..., description="Whether the language exists")
    label_group_exists: bool = Field(..., description="Whether the label group exists")
    label_code_exists: bool = Field(..., description="Whether the label code exists and belongs to group")
    message: str = Field(..., description="Validation message")


class LabelsForLanguageResponse(BaseModel):
    """Model for getting all labels for a specific language"""
    language_id: int
    language_name: str
    language_code: str
    labels: dict = Field(..., description="Dictionary of labels grouped by label groups")
    total_labels: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "language_id": 1,
                "language_name": "English",
                "language_code": "en",
                "labels": {
                    "home": {
                        "text_welcome": "Welcome to our website!",
                        "btn_get_started": "Get Started"
                    },
                    "navigation": {
                        "menu_home": "Home",
                        "menu_about": "About"
                    }
                },
                "total_labels": 4
            }
        }


# ======== BULK OPERATIONS MODELS ========

class BulkLabelItem(BaseModel):
    """Model for a single label in bulk operations"""
    label_code_name: str = Field(..., description="Name of the label code (e.g., 'text_welcome')")
    label_text: str = Field(..., description="Translated text for this label")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label_code_name": "text_welcome",
                "label_text": "Welcome to our website!"
            }
        }


class BulkLabelRequest(BaseModel):
    """Model for bulk label insertion request"""
    language_id: int = Field(..., description="ID of the language")
    label_group_id: int = Field(..., description="ID of the label group")
    labels: List[BulkLabelItem] = Field(..., description="List of labels to insert", min_items=1, max_items=100)
    allow_updates: bool = Field(default=False, description="Whether to update existing labels instead of failing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language_id": 1,
                "label_group_id": 1,
                "allow_updates": False,
                "labels": [
                    {
                        "label_code_name": "text_welcome",
                        "label_text": "Welcome to our website!"
                    },
                    {
                        "label_code_name": "btn_get_started",
                        "label_text": "Get Started"
                    }
                ]
            }
        }


class BulkLabelResult(BaseModel):
    """Model for a single label result in bulk operations"""
    label_code_name: str
    label_text: str
    success: bool
    message: str
    label_id: Optional[int] = None
    action: Optional[str] = Field(None, description="Action performed: 'inserted', 'updated', or 'skipped'")


class BulkLabelResponse(BaseModel):
    """Model for bulk label insertion response"""
    success: bool = Field(..., description="Overall success status")
    total_labels: int = Field(..., description="Total number of labels processed")
    successful_insertions: int = Field(..., description="Number of successfully inserted labels")
    successful_updates: int = Field(..., description="Number of successfully updated labels")
    failed_insertions: int = Field(..., description="Number of failed insertions")
    skipped_labels: int = Field(..., description="Number of skipped labels (existing without update)")
    results: List[BulkLabelResult] = Field(..., description="Detailed results for each label")
    message: str = Field(..., description="Overall message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_labels": 2,
                "successful_insertions": 1,
                "successful_updates": 1,
                "failed_insertions": 0,
                "skipped_labels": 0,
                "results": [
                    {
                        "label_code_name": "text_welcome",
                        "label_text": "Welcome to our website!",
                        "success": True,
                        "message": "Successfully inserted",
                        "label_id": 1,
                        "action": "inserted"
                    }
                ],
                "message": "Successfully processed 2 labels (1 inserted, 1 updated)"
            }
        } 