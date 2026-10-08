import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreate, JobStatusResponse
from app.services.pdf_generator import pdf_generator
from app.services.storage_service import storage_service
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

def create_job(db: Session, job_data: JobCreate) -> Job:
    total = len(job_data.recipients)
    job = Job(
        total_certificates=total,
        status=JobStatus.PENDING
    )
    db.add(job)
    db.flush()

    for recipient in job_data.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            course_name=job_data.course_name,
            completion_date=job_data.completion_date,
            status=CertificateStatus.PENDING
        )
        db.add(cert)
    
    db.commit()
    db.refresh(job)
    logger.info(f"Job {job.id} created with {total} certificates")
    return job

def get_job_status(db: Session, job_id: UUID) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None
    
    pending = job.total_certificates - (job.successful_certificates + job.failed_certificates)
    progress = 0
    if job.total_certificates > 0:
        progress = int(((job.successful_certificates + job.failed_certificates) / job.total_certificates) * 100)
        
    return {
        "job_id": job.id,
        "status": job.status,
        "total_certificates": job.total_certificates,
        "successful_certificates": job.successful_certificates,
        "failed_certificates": job.failed_certificates,
        "pending_certificates": pending,
        "progress_percentage": progress,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }

def get_job_history(db: Session) -> list[dict]:
    course_name = (
        db.query(Certificate.course_name)
        .filter(Certificate.job_id == Job.id)
        .order_by(Certificate.created_at)
        .limit(1)
        .scalar_subquery()
    )
    rows = db.query(Job, course_name.label("course_name")).order_by(Job.created_at.desc()).all()
    history = []

    for job, course in rows:
        pending = job.total_certificates - job.successful_certificates - job.failed_certificates
        completed = job.successful_certificates + job.failed_certificates
        progress = int(completed / job.total_certificates * 100) if job.total_certificates else 0
        history.append({
            "job_id": job.id,
            "course_name": course or "Untitled batch",
            "status": job.status,
            "total_certificates": job.total_certificates,
            "successful_certificates": job.successful_certificates,
            "failed_certificates": job.failed_certificates,
            "pending_certificates": pending,
            "progress_percentage": progress,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        })

    return history

def process_job_background(job_id: UUID):
    if isinstance(job_id, str):
        job_id = UUID(job_id)
        
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in background task")
            return
        
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        certificate_ids = [c_id for (c_id,) in db.query(Certificate.id).filter(Certificate.job_id == job_id).all()]
        
        for cert_id in certificate_ids:
            try:
                cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
                job = db.query(Job).filter(Job.id == job_id).first()
                
                cert.status = CertificateStatus.PROCESSING
                db.commit()
                
                logger.info(f"Generating certificate for {cert.recipient_email} in job {job_id}")
                file_path = storage_service.get_certificate_path(job_id, cert.recipient_name)
                
                pdf_generator.generate_certificate(
                    recipient_name=cert.recipient_name,
                    course_name=cert.course_name,
                    completion_date=cert.completion_date.strftime("%d %B %Y"),
                    output_path=file_path
                )
                
                cert.file_path = file_path
                cert.status = CertificateStatus.SUCCESS
                cert.generated_at = datetime.now(timezone.utc)
                job.successful_certificates += 1
                db.commit()
                logger.info(f"Certificate for {cert.recipient_email} generated successfully")
                
            except Exception as e:
                logger.error(f"Certificate generation failed for {cert.recipient_email if 'cert' in locals() and cert else cert_id}: {str(e)}")
                
                cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
                job = db.query(Job).filter(Job.id == job_id).first()
                
                if cert and job:
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = str(e)
                    job.failed_certificates += 1
                    db.commit()
                continue
                
        job = db.query(Job).filter(Job.id == job_id).first()
        if job.failed_certificates == 0 and job.successful_certificates > 0:
            job.status = JobStatus.COMPLETED
        elif job.successful_certificates == 0 and job.failed_certificates > 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED_WITH_ERRORS
            
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} completed with status {job.status}")
        
    except Exception as e:
        logger.error(f"Fatal error processing job {job_id}: {str(e)}")
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        db.close()
