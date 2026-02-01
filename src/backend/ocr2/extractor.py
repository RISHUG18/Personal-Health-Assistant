import re
from typing import List, Optional
from models import MedicalReport, PatientInfo, TestResult, SourceMetadata
import dateutil.parser

class MedicalExtractor:
    def __init__(self):
        self.test_patterns = [
            # Pattern: Name Value Unit Range (e.g., "Hemoglobin 13.5 g/dL 12-16")
            r"(?P<name>[a-zA-Z\s\(\)]+)\s+(?P<value>\d+(\.\d+)?)\s+(?P<unit>[a-zA-Z/%]+)\s+(?P<range>[\d\.\-\s]+)",
        ]

    def extract(self, text: str, confidence: float) -> MedicalReport:
        patient_info = self._extract_patient_info(text)
        tests = self._extract_tests(text)
        
        return MedicalReport(
            patient_info=patient_info,
            tests=tests,
            source_metadata=SourceMetadata(
                confidence_score=confidence,
                ocr_engine="tesseract"
            )
        )

    def _extract_patient_info(self, text: str) -> PatientInfo:
        name_match = re.search(r"Name:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
        date_match = re.search(r"Date:\s*([\d\/\-]+)", text, re.IGNORECASE)
        age_match = re.search(r"Age:\s*(\d+)", text, re.IGNORECASE)
        gender_match = re.search(r"Gender:\s*(Male|Female)", text, re.IGNORECASE)

        return PatientInfo(
            name=name_match.group(1).strip() if name_match else None,
            report_date=date_match.group(1).strip() if date_match else None,
            age=int(age_match.group(1)) if age_match else None,
            gender=gender_match.group(1).strip() if gender_match else None
        )

    def _extract_tests(self, text: str) -> List[TestResult]:
        tests = []
        lines = text.split('\n')
        
        # Mapping for normalization
        synonyms = {
            "hgb": "Hemoglobin",
            "hb": "Hemoglobin",
            "blood sugar": "Glucose",
        }

        for line in lines:
            line = line.strip()
            # Looks for: Testname Value Units [Reference Range]
            # Updated to capture optional reference range at the end
            match = re.search(r"([A-Za-z\s\(\)]+?)\s+(\d+\.?\d*)\s+([a-zA-Z\%\/0-9\^]+)\s*(.*)", line)
            if match:
                raw_name = match.group(1).strip()
                try:
                     value = float(match.group(2))
                except ValueError:
                     continue
                
                unit = match.group(3).strip()
                potential_range = match.group(4).strip()
                
                # Clean up reference range
                # Valid ranges usually have digits, <, >, or -
                ref_range = None
                if potential_range and re.search(r"[\d<>]", potential_range):
                     ref_range = potential_range
                
                # Minimum length check to avoid noise
                if len(raw_name) < 3:
                    continue

                # Normalize Name
                name = synonyms.get(raw_name.lower(), raw_name)
                
                # Determine Flag
                flag = "normal" 
                # Basic High/Low logic if range is "num-num"
                if ref_range and '-' in ref_range:
                    try:
                        parts = ref_range.split('-')
                        # naive parse
                        low = float(re.sub(r'[^\d\.]', '', parts[0]))
                        high = float(re.sub(r'[^\d\.]', '', parts[1]))
                        if value < low: flag = "low"
                        if value > high: flag = "high"
                    except:
                        pass
                
                tests.append(TestResult(
                    test_name=name,
                    value=value,
                    unit=unit,
                    reference_range=ref_range,
                    flag=flag,
                    confidence=0.8
                ))
        return tests
