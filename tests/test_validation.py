def test_invalid_email(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Python Backend",
            "completion_date": "2026-10-08",
            "recipients": [
                {"name": "John Doe", "email": "invalid-email"}
            ]
        }
    )
    assert response.status_code == 422

def test_missing_name(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Python Backend",
            "completion_date": "2026-10-08",
            "recipients": [
                {"email": "john@example.com"}
            ]
        }
    )
    assert response.status_code == 422

def test_empty_recipients(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Python Backend",
            "completion_date": "2026-10-08",
            "recipients": []
        }
    )
    assert response.status_code == 422

def test_invalid_date(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "course_name": "Python Backend",
            "completion_date": "invalid-date",
            "recipients": [
                {"name": "John", "email": "john@example.com"}
            ]
        }
    )
    assert response.status_code == 422

def test_missing_required_fields(client):
    response = client.post(
        "/api/v1/jobs",
        json={}
    )
    assert response.status_code == 422
