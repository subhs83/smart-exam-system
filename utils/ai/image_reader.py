import pytesseract
from PIL import Image
import pdfplumber
import os

# ===== Step 6: Set Tesseract path =====
# Make sure this points to your installed tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ===== IMAGE TEXT EXTRACTION =====
def extract_text_from_image(image_path):
    """
    Extracts text from a single image (jpg, png, jpeg).
    Returns string.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")
    
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()


# ===== PDF TEXT EXTRACTION =====
def extract_text_from_pdf(pdf_path, max_pages=5):
    """
    Extracts text from a PDF.
    max_pages: limits pages to avoid large PDFs.
    Returns string of combined text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_read = min(len(pdf.pages), max_pages)
        for i in range(pages_to_read):
            page = pdf.pages[i]
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text.strip()


# ===== UTILITY FUNCTION: AUTO DETECT =====
def extract_text(file_path):
    """
    Auto-detect file type and extract text.
    Supports PDF and images.
    """
    ext = file_path.split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext in ["png", "jpg", "jpeg"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported file type. Only PDF or image allowed.")


# ===== TESTING =====
if __name__ == "__main__":
    # Example usage
    pdf_test = "example.pdf"
    image_test = "example_page.jpg"

    print("===== PDF TEST =====")
    try:
        text = extract_text_from_pdf(pdf_test)
        print(text[:500])  # print first 500 chars
    except Exception as e:
        print(e)

    print("\n===== IMAGE TEST =====")
    try:
        text = extract_text_from_image(image_test)
        print(text[:500])
    except Exception as e:
        print(e)