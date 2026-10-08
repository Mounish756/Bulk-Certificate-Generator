import os
from unittest.mock import patch
from app.services import job_service

def test_failure_isolation(client, db):
    original_generate = job_service.pdf_generator.generate_certificate
    
    def mock_generate(recipient_name, course_name, completion_date, output_path):
        if recipient_name == "Fail User":
            raise Exception("Mocked generation failure")
        return original_generate(recipient_name, course_name, completion_date, output_path)

    with patch("app.services.job_service.pdf_generator.generate_certificate", side_effect=mock_generate):
        response = client.post(
            "/api/v1/jobs",
            json={
                "course_name": "Test Course",
                "completion_date": "2026-10-08",
                "recipients": [
                    {"name": "Success User", "email": "success@example.com"},
                    {"name": "Fail User", "email": "fail@example.com"},
                    {"name": "Another Success", "email": "success2@example.com"}
                ]
            }
        )
    job_id = response.json()["job_id"]
        
    res = client.get(f"/api/v1/jobs/{job_id}")
    data = res.json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["successful_certificates"] == 2
    assert data["failed_certificates"] == 1
    assert data["total_certificates"] == 3
