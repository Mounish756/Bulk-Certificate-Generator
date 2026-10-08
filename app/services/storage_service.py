import os
import re
from uuid import UUID

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")

class StorageService:
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        # Keep only alphanumeric and spaces, replace spaces with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
        return clean_name.strip().replace(" ", "_").lower()

    @staticmethod
    def get_certificate_path(job_id: UUID, recipient_name: str) -> str:
        job_dir = os.path.join(GENERATED_DIR, str(job_id))
        os.makedirs(job_dir, exist_ok=True)
        
        safe_name = StorageService._sanitize_filename(recipient_name)
        filename = f"{safe_name}_certificate.pdf"
        
        return os.path.join(job_dir, filename)

storage_service = StorageService()
