# =======================
# app/utils/text_chunking.py
# =======================
from typing import List

class TextChunker:
    """Alternative text chunking strategies."""

    @staticmethod
    def chunk_by_sentences(text: str, max_chunk_size: int = 1000) -> List[str]:
        """Chunk text by sentences, respecting max size."""
        import re
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    @staticmethod
    def chunk_by_paragraphs(text: str, max_chunk_size: int = 1000) -> List[str]:
        """Chunk text by paragraphs, respecting max size."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks
