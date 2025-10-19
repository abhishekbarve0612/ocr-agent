from __future__ import annotations
from optparse import Option
import os
import mimetypes
from dataclasses import dataclass
from typing import Optional, List, Tuple

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeResult,
    AnalyzeDocumentRequest,
)

import dotenv

dotenv.load_dotenv()


@dataclass
class AzureOCRPage:
    page_number: int
    text: str
    span: Tuple[int, int]
    
@dataclass
class AzureOCRResponse:
    result: AnalyzeResult
    full_text: str
    pages: List[AzureOCRPage]
    
class AzureOCR:
    def __init__(self) -> None:
        key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        if not key or not endpoint:
            raise RuntimeError('Azure Document Intelligence key and endpoint are missing')
        self._client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )
        
    def analyze_file(self, path: str, *, pages: Option[str] = None) -> AzureOCRResponse:
        model_id = 'prebuilt-read'
        output_format = 'text'
        
        ctype, _ = mimetypes.guess_type(path)
        content_type = ctype or 'application/octet-stream'
        
        with open(path, 'rb') as f:
            poller = self._client.begin_analyze_document(
                model_id=model_id,
                body=f,
                content_type=content_type,
                pages=pages,
                output_content_format=output_format,
            )
        
        result: AnalyzeResult = poller.result()
        
        print(f"Result--------------------..........................: {result}")
        content = result.content or ''
        pages_out: List[AzureOCRPage] = []
        
        for idx, page in enumerate(result.pages or []):
            span0 = page.spans[0]
            offset = span0['offset'] if isinstance(span0, dict) else span0.offset
            length = span0['length'] if isinstance(span0, dict) else span0.length
            page_text = content[offset: offset + length]
            pages_out.append(
                AzureOCRPage(
                    page_number=idx + 1,
                    text=page_text,
                    span=(offset, length),
                )
            )
        
        return AzureOCRResponse(result=result, full_text=content, pages=pages_out)
        
