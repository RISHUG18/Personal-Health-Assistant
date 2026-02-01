from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import ValidationError
import uvicorn
import shutil
import os
import cv2
import numpy as np
from uuid import uuid4

from models import MedicalReport
from preprocessor import preprocess_image
from ocr_engine import run_ocr
from extractor import MedicalExtractor

app = FastAPI(title="Medical OCR API")

# Storage for demo purposes (In-Memory)
STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
reports_db = {}

@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    file_id = str(uuid4())
    file_path = os.path.join(STORAGE_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    reports_db[file_id] = {"path": file_path, "status": "uploaded"}
    return {"id": file_id, "message": "File uploaded successfully"}

from pdf2image import convert_from_path

# ... (rest of imports)

from fastapi.responses import PlainTextResponse

# ... (imports)

@app.post("/run-ocr/{report_id}", response_class=PlainTextResponse)
async def run_ocr_endpoint(report_id: str):
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
        
    file_path = reports_db[report_id]["path"]
    
    full_text = ""
    total_confidence = 0.0
    page_count = 0

    # Check for PDF
    if file_path.lower().endswith('.pdf'):
        try:
            pil_images = convert_from_path(file_path)
            
            for i, pil_image in enumerate(pil_images):
                open_cv_image = np.array(pil_image) 
                image = open_cv_image[:, :, ::-1].copy() 
                
                processed_image = preprocess_image(image)
                text, confidence = run_ocr(processed_image)
                
                full_text += f"\n--- Page {i+1} ---\n{text}"
                total_confidence += confidence
                page_count += 1
            
            avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

    else:
        image = cv2.imread(file_path)
        if image is None:
             raise HTTPException(status_code=400, detail="Could not read image file")
         
        processed_image = preprocess_image(image)
        full_text, avg_confidence = run_ocr(processed_image)
    
    reports_db[report_id]["ocr_text"] = full_text
    reports_db[report_id]["confidence"] = avg_confidence
    reports_db[report_id]["status"] = "ocr_completed"
    
    return full_text

@app.post("/extract-medical-data/{report_id}", response_model=MedicalReport)
async def extract_data(report_id: str):
    if report_id not in reports_db:
         raise HTTPException(status_code=404, detail="Report not found")
         
    if "ocr_text" not in reports_db[report_id]:
         raise HTTPException(status_code=400, detail="Run OCR first")
         
    text = reports_db[report_id]["ocr_text"]
    confidence = reports_db[report_id]["confidence"]
    
    extractor = MedicalExtractor()
    data = extractor.extract(text, confidence)
    
    reports_db[report_id]["extracted_data"] = data
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
