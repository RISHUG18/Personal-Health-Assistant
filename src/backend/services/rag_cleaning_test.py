import os
from text_cleaning import clean_full_text
from chunking import doc_to_chunks

SAMPLE_PATH="sample_ocr.txt"

def main():
    if not os.path.exists(SAMPLE_PATH):
        print("sample_ocr.txt not found")
        return

    with open(SAMPLE_PATH,"r",encoding="utf-8") as f:
        raw=f.read()

    print("\n===== RAW SAMPLE =====\n")
    print(raw[:500])
    print("\n======================\n")

    # CLEAN TEXT
    cleaned=clean_full_text(raw)

    print("\n===== CLEANED TEXT LENGTH =====")
    print(len(cleaned))
    print("===============================\n")

    print("\n===== CLEANED TEXT SAMPLE =====\n")
    print(cleaned[:800])
    print("\n===============================\n")

    if len(cleaned.strip())==0:
        print("❌ Cleaning returned empty")
        return

    # CHUNKING
    chunks=doc_to_chunks(cleaned)

    print("\nTOTAL CHUNKS:",len(chunks))

    for i,c in enumerate(chunks[:10]):
        print(f"\n--- CHUNK {i+1} ---")
        print(c)

    # save to file
    with open("sample_chunks.txt","w") as f:
        for c in chunks:
            f.write(c+"\n\n")

    print("\nChunks saved to sample_chunks.txt")

if __name__=="__main__":
    main()
