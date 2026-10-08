import os
from app.services.pdf_generator import pdf_generator
import tempfile

def test_pdf_generation():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        temp_path = f.name
        
    try:
        pdf_generator.generate_certificate(
            recipient_name="John Doe",
            course_name="Test Course",
            completion_date="08 October 2026",
            output_path=temp_path
        )
        
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
