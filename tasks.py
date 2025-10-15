import os
from generate_pdf import generate_daily_log_pdf

def generate_pdf_task(form_data, image_paths, output_path):
    # Call your existing PDF function
    return generate_daily_log_pdf(form_data, image_paths, output_path)