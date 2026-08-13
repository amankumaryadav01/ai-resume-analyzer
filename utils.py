import io
import pypdf
import docx

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from PDF bytes."""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
        return "\n".join(text).strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text content from DOCX bytes."""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        return "\n".join(text).strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

def extract_resume_text(uploaded_file) -> str:
    """Determine file extension and extract text accordingly."""
    if uploaded_file is None:
        raise ValueError("Uploaded file is empty.")

    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

    if not text.strip():
        raise ValueError("Extracted resume text is empty. Please check the file content.")

    return text