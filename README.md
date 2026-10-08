# Bulk Certificate Generator Backend

A robust REST API built with FastAPI to handle the bulk generation of PDF certificates asynchronously. 
The system accepts a single request with a list of recipients, creates generation jobs, and processes individual certificates in the background. It employs individual failure isolation, meaning if one certificate generation fails, the rest will continue processing undisturbed.

## Features
- **Bulk Job Creation**: Accept a large list of recipients in a single request.
- **Asynchronous Processing**: Immediate API response while PDF generation happens in the background.
- **Failure Isolation**: A single corrupted recipient won't halt the entire job.
- **Status Tracking**: Query job progress, successful, and failed certificate counts.
- **Certificate Retrieval**: Download generated PDF certificates directly via the API.
- **Robust Validation**: Ensures data integrity with Pydantic schemas (e.g., valid email formatting).

## Architecture & Technology Choices
- **FastAPI**: Selected for its modern, fast, and asynchronous nature out-of-the-box. It provides excellent automatic OpenAPI documentation (`/docs`).
- **PostgreSQL**: A robust relational database standard for reliable state tracking.
- **SQLAlchemy 2.x & Alembic**: Industry standard ORM and migration tool for Python.
- **ReportLab**: Chosen for programmatically generating PDF certificates efficiently.
- **BackgroundTasks**: FastAPI's built-in background tasks are used to process certificates asynchronously without blocking the main event loop, keeping the implementation simple. For a massive scale production scenario, this architecture cleanly separates logic in `job_service.py` making it trivial to drop in Celery/Redis later.

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (if running locally without Docker)

### 1. Environment Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```

### 2. Running with Docker (Recommended)
This starts both the FastAPI application and the PostgreSQL database.
```bash
docker-compose up --build
```
*Note: The Dockerfile is configured to automatically run `alembic upgrade head` upon startup, initializing all database tables.*

### 3. Local Development (Without Docker)
1. Start a local PostgreSQL instance and update `.env` to point to it.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation
Once running, navigate to `http://localhost:8000/docs` to view the interactive OpenAPI documentation.

### Core Endpoints

**1. Health Check**
`GET /health`
Returns system status.

**2. Create Bulk Job**
`POST /api/v1/jobs`
```json
{
  "course_name": "Python Backend Development",
  "completion_date": "2026-10-08",
  "recipients": [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
  ]
}
```

**3. Check Job Status**
`GET /api/v1/jobs/{job_id}`
Returns progress percentage, statuses, and counts.

**4. List Certificates for Job**
`GET /api/v1/jobs/{job_id}/certificates`
Lists all individual certificates and their statuses.

**5. Retrieve Generated Certificate**
`GET /api/v1/certificates/{certificate_id}`
Returns the generated PDF file if generation was successful.

## Running Tests
Tests use Pytest, HTTPX, and an in-memory SQLite database to avoid interfering with production data.
```bash
pytest
```

## Design Decisions
- **Failure Handling**: Loop over each certificate in a `try...except` block in the background service (`job_service.py`). Upon exception, that specific certificate's state is updated to `FAILED`, the DB session is rolled back for that small unit, and the loop `continue`s to the next recipient.
- **Background Processing**: FastAPI `BackgroundTasks` was used as it completely satisfies the requirement of offloading processing from the request cycle without adding the heavy complexity of Redis and Celery. 
- **Storage**: Files are saved to a local `./generated/{job_id}/` directory. The filename is sanitized using regular expressions to prevent path traversal and ensure filesystem safety. 
- **Database Models**: Storing job progress (successful/failed counts) directly on the `Job` model using aggregate updates during processing allows `GET /api/v1/jobs/{job_id}` to respond instantly without needing complex aggregate SQL queries across potentially tens of thousands of certificates.

## Future Improvements
- Implement AWS S3 integration in `storage_service.py` to replace local filesystem storage.
- Migrate from FastAPI `BackgroundTasks` to Celery & Redis if the node becomes CPU-bottlenecked handling PDF generation for massive jobs.
- Add pagination support to the `GET /api/v1/jobs/{job_id}/certificates` endpoint.
