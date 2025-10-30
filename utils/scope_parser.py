import os
from docx import Document
import pdfplumber
import pandas as pd

def parse_scope_file(filepath):
    ext = os.path.splitext(filepath)[-1].lower()

    if ext == ".txt":
        with open(filepath, "r") as f:
            lines = f.readlines()
    elif ext == ".docx":
        doc = Document(filepath)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
    elif ext == ".pdf":
        lines = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                lines += page.extract_text().split("\n")
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(filepath)
        lines = df.astype(str).apply(lambda row: " ".join(row), axis=1).tolist()
    else:
        lines = []

    return [l.strip() for l in lines if l.strip()]
