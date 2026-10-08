import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum, Text, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base

class CertificateStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(Uuid(as_uuid=True), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    course_name = Column(String(255), nullable=False)
    completion_date = Column(Date, nullable=False)
    
    status = Column(String, default=CertificateStatus.PENDING, nullable=False)
    file_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_at = Column(DateTime, nullable=True)

    job = relationship("Job", back_populates="certificates")
