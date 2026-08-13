from pypdf import PdfReader
import docx


def extract_resume_text(uploaded_file) -> str:
    """Extract text from PDF or DOCX resume."""
    uploaded_file.seek(0)

    filename = getattr(uploaded_file, "name", "").lower()

    if filename.endswith(".docx"):
        document = docx.Document(uploaded_file)

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n".join(text_parts)

    raise ValueError(
        "Unsupported file format. Please upload a PDF or DOCX file."
    )
