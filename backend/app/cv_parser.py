import io
from typing import Tuple, List
import docx
from pypdf import PdfReader

from app.models import CVProfile, CVParseResponse
from app.llm_client import extract_profile_with_llm


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_chunks: List[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_chunks.append(extracted)
    return "\n".join(text_chunks)


def extract_text_from_docx(docx_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(docx_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text])


def extract_raw_text(file_bytes: bytes, filename: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
    elif lower_name.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported format. Only .pdf and .docx are supported.")

    if not raw_text.strip():
        warnings.append("Warning: Could not extract text from document.")

    return raw_text.strip(), warnings


async def parse_cv(file_bytes: bytes, filename: str) -> CVParseResponse:
    raw_text, warnings = extract_raw_text(file_bytes, filename)
    
    if not raw_text:
        return CVParseResponse(
            profile=CVProfile(full_name="Unknown"),
            source_filename=filename,
            warnings=["Document is empty or text could not be read."]
        )

    profile_data = await extract_profile_with_llm(raw_text)
    profile_data.raw_text_char_count = len(raw_text)

    return CVParseResponse(
        profile=profile_data,
        source_filename=filename,
        warnings=warnings
    )