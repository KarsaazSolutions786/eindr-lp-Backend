from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


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