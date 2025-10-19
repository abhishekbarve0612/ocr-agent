from dataclasses import dataclass
from typing import List, Tuple

PageText = Tuple[int, str]

@dataclass
class ChunkOutput:
    pages_str: str
    input_tokens: int
    output_tokens: int
    markdown: str

@dataclass
class FormatDocResult:
    chunks: List[ChunkOutput]
    total_input_tokens: int
    total_output_tokens: int
    combined_markdown: str
