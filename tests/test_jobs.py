def test_create_job(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Python Backend",
            "completion_date": "2026-10-08",
            "recipients": [
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Doe", "email": "jane@example.com"}
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["total_certificates"] == 2
