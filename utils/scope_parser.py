# scope_parser.py
# Phase 2B: Scope Parser for PDF, DOCX, XLSX, PPTX formats

import os
import json
import fitz  # PyMuPDF
import docx
import openpyxl
from pptx import Presentation
from typing import List

def clean_text(text: str) -> List[str]:
    lines = [line.strip("-• ") for line in text.split("\n") if len(line.strip()) > 5]
    return list(dict.fromkeys(lines))  # Remove duplicates, preserve order

def extract_pdf_scope(path: str) -> List[str]:
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return clean_text(text)

def extract_docx_scope(path: str) -> List[str]:
    doc = docx.Document(path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    return clean_text(full_text)

def extract_xlsx_scope(path: str) -> List[str]:
    wb = openpyxl.load_workbook(path)
    text = ""
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if cell and isinstance(cell, str) and len(cell.strip()) > 3:
                    text += str(cell) + "\n"
    return clean_text(text)

def extract_pptx_scope(path: str) -> List[str]:
    prs = Presentation(path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return clean_text(text)

def parse_scope_file(file_path: str, project_id: str) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext.endswith(".pdf"):
        checklist = extract_pdf_scope(file_path)
    elif ext.endswith(".docx"):
        checklist = extract_docx_scope(file_path)
    elif ext.endswith(".xlsx"):
        checklist = extract_xlsx_scope(file_path)
    elif ext.endswith(".pptx"):
        checklist = extract_pptx_scope(file_path)
    else:
        raise ValueError("Unsupported scope file format")

    # Filter out generic items
    ignore_phrases = ["project management", "superintendent", "contracts administration", "cleanup"]
    checklist = [item for item in checklist if not any(x.lower() in item.lower() for x in ignore_phrases)]

    result = {
        "project_id": project_id,
        "checklist": checklist
    }
    os.makedirs("scope_data", exist_ok=True)
    with open(f"scope_data/{project_id}.json", "w") as f:
        json.dump(result, f, indent=2)
    return result

if __name__ == "__main__":
    print("Run from app.py with file path and project_id.")
