"""
Test full pipeline using OCR text from Supabase instead of local file.
Flow:
Supabase OCR text → clean → chunk → print
"""

from backend.config.supabase_client import get_supabase_client,get_ocr_reports_table
from backend.services.preprocessing.text_cleaning import clean_full_text
from backend.services.preprocessing.chunking import doc_to_chunks


def fetch_ocr_text(report_id:str)->str:
    """Fetch OCR text from Supabase table"""
    client=get_supabase_client()
    table=get_ocr_reports_table()

    res=client.table(table).select("ocr_text").eq("id",report_id).execute()

    if not res.data:
        return ""

    return res.data[0]["ocr_text"] or ""


def main():
    print("\nEnter report_id from Supabase:")
    report_id=input(">> ").strip()

    raw=fetch_ocr_text(report_id)

    if not raw:
        print("\n❌ No OCR text found for this ID")
        return

    print("\n===== OCR TEXT (first 500 chars) =====\n")
    print(raw[:500])
    print("\n======================================\n")

    # CLEAN
    cleaned=clean_full_text(raw)

    print("\n===== CLEANED LENGTH =====")
    print(len(cleaned))
    print("==========================\n")

    # CHUNK
    chunks=doc_to_chunks(cleaned)

    print("\nTOTAL CHUNKS:",len(chunks))

    for i,c in enumerate(chunks[:10]):
        print(f"\n--- CHUNK {i+1} ---")
        print(c)


if __name__=="__main__":
    main()
