import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

class PDFGeneratorService:
    @staticmethod
    def generate_certificate(recipient_name: str, course_name: str, completion_date: str, output_path: str):
        # We ensure the directory exists just in case
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        c = canvas.Canvas(output_path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Simple template
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width / 2.0, height - 1.5 * inch, "CERTIFICATE OF COMPLETION")
        
        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2.0, height - 2.5 * inch, "This certificate is proudly presented to")
        
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width / 2.0, height - 3.5 * inch, recipient_name)
        
        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2.0, height - 4.5 * inch, "for successfully completing")
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2.0, height - 5.5 * inch, course_name)
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2.0, height - 6.5 * inch, "Date of Completion:")
        c.drawCentredString(width / 2.0, height - 7.0 * inch, completion_date)
        
        # Border
        c.setLineWidth(5)
        c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
        
        c.save()

pdf_generator = PDFGeneratorService()
