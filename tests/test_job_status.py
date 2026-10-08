from app.services import job_service
import os

def test_job_processing_success(client, db):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Test Course",
            "completion_date": "2026-10-08",
            "recipients": [
                {"name": "Alice", "email": "alice@example.com"}
            ]
        }
    )
    job_id = response.json()["job_id"]
    
    res = client.get(f"/api/v1/jobs/{job_id}")
    data = res.json()
    
    assert data["status"] == "COMPLETED"
    assert data["successful_certificates"] == 1
    assert data["failed_certificates"] == 0
    assert data["progress_percentage"] == 100
