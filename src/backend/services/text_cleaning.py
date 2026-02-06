import re
from typing import List

# detect measurement-like patterns
MEASUREMENT_RE = re.compile(
    r"[A-Za-z][A-Za-z \(\)\/\-]+?\s+[0-9]+(?:\.[0-9]+)?\s*(?:mg/dL|g/dL|U/L|%|mmol|mEq|pg|nmol|thou|cells|fL|pg/mL|ng/mL|IU/L)?",
    re.IGNORECASE
)

# junk patterns to remove
JUNK_PATTERNS = [
    r"Collected at",
    r"Processed at",
    r"National Reference laboratory",
    r"Test Report",
    r"Page\s*\d+",
    r"Dr\.",
    r"Authorized",
    r"IMPORTANT INSTRUCTIONS",
]

def break_into_lines(raw:str)->List[str]:
    """
    OCR often returns one giant paragraph.
    We split using measurement patterns and punctuation.
    """
    # Replace weird OCR separators
    raw=raw.replace("  "," ")
    raw=raw.replace("\t"," ")

    # split where measurement likely begins
    parts=re.split(r"(?=[A-Z][A-Za-z \(\)\/\-]{2,}\s+[0-9])",raw)

    lines=[]
    for p in parts:
        p=p.strip()
        if len(p)<3:
            continue
        lines.append(p)
    return lines

def remove_junk(lines:List[str])->List[str]:
    cleaned=[]
    for line in lines:
        drop=False
        for pat in JUNK_PATTERNS:
            if re.search(pat,line,re.IGNORECASE):
                drop=True
                break
        if not drop:
            cleaned.append(line.strip())
    return cleaned

def clean_full_text(raw:str)->str:
    # STEP 1: break giant OCR text into logical lines
    lines=break_into_lines(raw)

    # STEP 2: remove junk headers
    lines=remove_junk(lines)

    # STEP 3: keep only meaningful lines
    final=[]
    for l in lines:
        if MEASUREMENT_RE.search(l) or len(l)>25:
            final.append(l)

    return "\n".join(final)
