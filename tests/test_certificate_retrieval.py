from app.services import job_service

def test_certificate_retrieval(client, db):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Test Course",
            "completion_date": "2026-10-08",
            "recipients": [
                {"name": "Bob", "email": "bob@example.com"}
            ]
        }
    )
    job_id = response.json()["job_id"]
    
    cert_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    certs = cert_res.json()["certificates"]
    assert len(certs) == 1
    
    cert_id = certs[0]["id"]
    
    # Retrieve PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

def test_retrieve_nonexistent(client):
    from uuid import uuid4
    res = client.get(f"/api/v1/certificates/{uuid4()}")
    assert res.status_code == 404
