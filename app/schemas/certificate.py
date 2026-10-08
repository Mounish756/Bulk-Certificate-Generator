from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import List, Optional

class CertificateResponse(BaseModel):
    id: UUID
    recipient_name: str
    recipient_email: EmailStr
    status: str
    error_message: Optional[str] = None

class CertificateListResponse(BaseModel):
    job_id: UUID
    certificates: List[CertificateResponse]
