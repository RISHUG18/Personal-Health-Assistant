from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    report_date: Optional[str] = None

class TestResult(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    flag: Literal["normal", "low", "high"]
    confidence: float

    class Config:
        json_schema_extra = {
            "example": {
                "test_name": "Hemoglobin",
                "value": 13.2,
                "unit": "g/dL",
                "reference_range": "13.0-17.0",
                "flag": "normal",
                "confidence": 0.95
            }
        }

class SourceMetadata(BaseModel):
    document_type: str = "lab_report"
    ocr_engine: str = "tesseract"
    language: str = "en"
    confidence_score: float

class MedicalReport(BaseModel):
    patient_info: PatientInfo
    tests: List[TestResult]
    source_metadata: SourceMetadata
