from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID

from app.core.config import settings

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Recipient's full name")
    email: EmailStr = Field(..., description="Recipient's email address")

class JobCreate(BaseModel):
    course_name: str = Field(..., min_length=1, max_length=255, description="Name of the course")
    completion_date: date = Field(..., description="Date of completion")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipients")

    @field_validator('recipients')
    @classmethod
    def check_recipients_limit(cls, v):
        if len(v) > settings.MAX_RECIPIENTS_PER_JOB:
            raise ValueError(f"Number of recipients cannot exceed {settings.MAX_RECIPIENTS_PER_JOB}")
        return v

class JobResponse(BaseModel):
    job_id: UUID
    status: str
    total_certificates: int

class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    total_certificates: int
    successful_certificates: int
    failed_certificates: int
    pending_certificates: int
    progress_percentage: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @field_validator('progress_percentage', mode='before')
    @classmethod
    def calculate_progress(cls, v, values):
        # We compute this at the service level, but can ensure it's here
        return v

class JobHistoryResponse(JobStatusResponse):
    course_name: str
