import os
import pymupdf4llm
from ingest_pnpk import PDF_METADATA_MAP

def test_parsing():
    print("Testing advanced PDF parsing with PyMuPDF4LLM...")
    
    # Path to one of the PDFs
    pdf_path = os.path.join("Data RAG", "PNPK_Diabetes.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        return 1
        
    try:
        # We use page_chunks=True to get a list of dicts with 'text' and 'metadata'
        md_text = pymupdf4llm.to_markdown(pdf_path, pages=[0, 1, 2, 3])
        print("Success! Extracted markdown snippet:")
        print("-" * 50)
        # Print a snippet of the extracted markdown
        print(md_text[:1000])
        print("-" * 50)
        
        # Check if table formatting is present (look for '|' and '-')
        if "|" in md_text:
            print("\n✅ Verification Passed: Table or markdown structure detected!")
            return 0
        else:
            print("\n⚠️ Note: No table found in the first few pages, but parsing was successful.")
            return 0
    except Exception as e:
        print(f"\n❌ Error during parsing: {e}")
        return 1

if __name__ == "__main__":
    exit(test_parsing())
