import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobcard_system.settings')
django.setup()

from jobcards.views import generate_dummy_pdf_buffer

try:
    generate_dummy_pdf_buffer()
    print("PDF GENERATION SUCCESS")
except Exception as e:
    print(f"PDF GENERATION FAILED: {e}")
