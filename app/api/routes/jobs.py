from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas.job import JobCreate, JobHistoryResponse, JobResponse, JobStatusResponse
from app.schemas.certificate import CertificateListResponse, CertificateResponse
from app.services import job_service
from app.models.certificate import Certificate

router = APIRouter()

@router.get("", response_model=list[JobHistoryResponse])
def list_jobs(db: Session = Depends(get_db)):
    return job_service.get_job_history(db)

@router.post("", response_model=JobResponse, status_code=201)
def create_bulk_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        job = job_service.create_job(db, job_in)
        background_tasks.add_task(job_service.process_job_background, job.id)
        return JobResponse(
            job_id=job.id,
            status=job.status,
            total_certificates=job.total_certificates
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    status_data = job_service.get_job_status(db, job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return status_data

@router.get("/{job_id}/certificates", response_model=CertificateListResponse)
def list_job_certificates(job_id: UUID, db: Session = Depends(get_db)):
    status_data = job_service.get_job_status(db, job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Generation job not found")
        
    certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    
    cert_responses = [
        CertificateResponse(
            id=c.id,
            recipient_name=c.recipient_name,
            recipient_email=c.recipient_email,
            status=c.status,
            error_message=c.error_message
        ) for c in certificates
    ]
    
    return CertificateListResponse(
        job_id=job_id,
        certificates=cert_responses
    )
