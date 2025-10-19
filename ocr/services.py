from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List, Tuple
from PIL import Image

import io, mimetypes
import fitz # PyMuPDF
import pytesseract

from .models import OCRPage
from .azure_ocr import AzureOCR

MIN_TEXT_LENGTH = 20
RASTER_ZOOM = 2.5 # ~360-450 DPI Equivalent

@dataclass
class OCRResult:
    page_number: int
    source: str
    text: str
    average_confidence: float | None = None
    
    def __str__(self):
        return f"Page {self.page_number} - {self.source} - {self.text[:50]}..."
    
def _is_pdf(path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(path)
    return (mime_type == 'application/pdf') or path.lower().endswith('.pdf')

def parse_page_range(spec: str | None, total_pages: int) -> List[int]:
    if not spec or spec.strip().lower() == 'all':
        return list(range(1, total_pages + 1))
    
    pages: List[int] = []
    for token in spec.split(','):
        token = token.strip()
        if '-' in token:
            a, b = token.split('-', 1)
            start = max(1, int(a))
            end = min(total_pages, int(b))
            if start <= end:
                pages.extend(range(start, end + 1))
        else:
            p = int(token)
            if 1 <= p <= total_pages:
                pages.append(p)
    return sorted(set(pages))

def _image_to_text_and_confidence(image: Image.Image, language: str) -> Tuple[str, float | None]:
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, lang=language, config=custom_config) or ''
    data = pytesseract.image_to_data(
        image,
        lang=language,
        output_type=pytesseract.Output.DICT,
    )
    confidences = [int(c) for c in data.get('conf', []) if c not in ('-1', -1)]
    return text.strip(), (mean(confidences) if confidences else None)

def _pixelmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')

def get_ocr_doc_results(
    path: str,
    page_range_spec: str | None,
    languages: str = 'eng',
) -> Iterable[OCRResult]:
    if _is_pdf(path):
        with fitz.open(path) as doc:
            total = len(doc)
            print(f"Total pages: {total}")
            for page_number in parse_page_range(page_range_spec, total):
                page = doc[page_number - 1]
                text_layer = (page.get_text('text') or '').strip()
                if len(text_layer) >= MIN_TEXT_LENGTH:
                    yield OCRResult(
                        page_number,
                        OCRPage.Source.PDF_TEXT,
                        text_layer,
                        None,
                    )
                    continue
                matrix = fitz.Matrix(RASTER_ZOOM, RASTER_ZOOM)
                pixels = page.get_pixmap(matrix=matrix, alpha=False)
                image = _pixelmap_to_pil(pixels)
                text, confidence = _image_to_text_and_confidence(image, languages)
                print(f"Text: {text} Confidence: {confidence} Page Number: {page_number}")
                yield OCRResult(
                    page_number,
                    OCRPage.Source.OCR,
                    text,
                    confidence,
                )
    else:
        image = Image.open(path).convert('RGB')
        text, confidence = _image_to_text_and_confidence(image, languages)
        yield OCRResult(
            1,
            OCRPage.Source.OCR,
            text,
            confidence,
        )
        

def azure_read_text(
    path: str, pages: str | None = None,
) -> list[tuple[int, str]]:
    client = AzureOCR()
    response = client.analyze_file(path, pages=pages)
    print(f"Azure analyze: pages={len(response.pages)}, chars={len(response.full_text or '')}")

    raw_pages = list(getattr(response.result, "pages", []) or [])

    for i, az_page in enumerate(response.pages):
        avg_conf = None
        if i < len(raw_pages):
            words = getattr(raw_pages[i], "words", None) or []
            confs = []
            for w in words:
                c = w["confidence"] if isinstance(w, dict) else getattr(w, "confidence", None)
                if isinstance(c, (int, float)):
                    confs.append(float(c))
            if confs:
                avg_conf = sum(confs) / len(confs)

        yield OCRResult(
            page_number=az_page.page_number,
            source=OCRPage.Source.OCR,
            text=az_page.text,
            average_confidence=avg_conf,
        )