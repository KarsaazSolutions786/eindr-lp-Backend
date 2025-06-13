from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class EmailSubmissionRequest(BaseModel):
    email: EmailStr
    
    @validator("email")
    def validate_email_format(cls, v):
        # Additional email validation if needed
        email_str = str(v).lower().strip()
        if len(email_str) > 255:
            raise ValueError("Email address is too long")
        return email_str


class EmailSubmissionResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class EmailRecord(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0" 