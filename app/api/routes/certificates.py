import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.certificate import Certificate, CertificateStatus

router = APIRouter()

@router.get("/{certificate_id}")
def get_certificate(certificate_id: UUID, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.status == CertificateStatus.PENDING or cert.status == CertificateStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Certificate is still being processed")
        
    if cert.status == CertificateStatus.FAILED:
        raise HTTPException(status_code=400, detail="Certificate generation failed and cannot be downloaded")
        
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")
        
    return FileResponse(
        path=cert.file_path,
        filename=os.path.basename(cert.file_path),
        media_type="application/pdf"
    )
