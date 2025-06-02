# =======================
# app/utils/document_processing.py
# =======================
import asyncio
from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path
import pypdf


logger = structlog.get_logger()


class DocumentProcessor:
    """PDF processing utilities for document extraction and chunking."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_pdf(self, file_path: str, document_id: str) -> List[Dict[str, Any]]:
        """Process PDF file: extract text and create chunks."""
        try:
            # Extract text from PDF
            text = await self._extract_pdf_text(file_path)
            
            if not text.strip():
                logger.warning("No text extracted from PDF", document_id=document_id)
                return []
            
            # Create chunks
            chunks = await self._chunk_text(text, document_id)
            
            logger.info("PDF processed successfully", 
                       document_id=document_id, 
                       chunks_created=len(chunks),
                       text_length=len(text))
            
            return chunks
            
        except Exception as e:
            logger.error("PDF processing failed", 
                        document_id=document_id, 
                        error=str(e))
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file using pypdf."""
        if not pypdf:
            raise ImportError("pypdf not available. Install with: pip install pypdf")
        
        def _extract():
            try:
                with open(file_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    text_parts = []
                    
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                text_parts.append(f"\n[Página {page_num + 1}]\n{page_text}")
                        except Exception as e:
                            logger.warning("Failed to extract text from page", 
                                         page=page_num, error=str(e))
                            continue
                    
                    return "\n".join(text_parts)
                    
            except Exception as e:
                logger.error("PDF text extraction failed", file_path=file_path, error=str(e))
                raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract)
    
    async def _chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks for embeddings."""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If we're not at the end, try to break at a good boundary
            if end < len(text):
                # Try to break at paragraph boundary first
                paragraph_break = text.rfind('\n\n', start, end)
                if paragraph_break > start + (self.chunk_size * 0.3):
                    end = paragraph_break
                else:
                    # Try to break at sentence boundary
                    sentence_break = text.rfind('.', start, end)
                    if sentence_break > start + (self.chunk_size * 0.5):
                        end = sentence_break + 1
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                # Extract page number if present
                page_number = self._extract_page_number(chunk_text)
                
                # Clean up the chunk text
                clean_text = self._clean_chunk_text(chunk_text)
                
                if clean_text and len(clean_text) > 50:  # Only include substantial chunks
                    chunks.append({
                        'document_id': document_id,
                        'content': clean_text,
                        'chunk_index': chunk_index,
                        'page_number': page_number,
                        'start_char': start,
                        'end_char': end,
                        'character_count': len(clean_text)
                    })
                    chunk_index += 1
            
            # Move to next chunk with overlap
            start = max(end - self.chunk_overlap, start + 1)
            
            # Safety check to prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _extract_page_number(self, text: str) -> Optional[int]:
        """Try to extract page number from chunk text."""
        import re
        
        # Look for [Página X] pattern
        page_match = re.search(r'\[Página (\d+)\]', text)
        if page_match:
            try:
                return int(page_match.group(1))
            except ValueError:
                pass
        
        return None
    
    def _clean_chunk_text(self, text: str) -> str:
        """Clean and normalize chunk text."""
        # Remove page markers
        import re
        text = re.sub(r'\[Página \d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove very short lines that might be noise
        lines = text.split('\n')
        clean_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(clean_lines).strip()
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        if not pypdf:
            return {}
        
        def _extract_metadata():
            try:
                with open(file_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    
                    metadata = {
                        'page_count': len(reader.pages),
                        'title': None,
                        'author': None,
                        'subject': None,
                        'creator': None
                    }
                    
                    # Extract PDF metadata if available
                    if reader.metadata:
                        metadata.update({
                            'title': reader.metadata.get('/Title'),
                            'author': reader.metadata.get('/Author'),
                            'subject': reader.metadata.get('/Subject'),
                            'creator': reader.metadata.get('/Creator')
                        })
                    
                    return metadata
                    
            except Exception as e:
                logger.warning("Metadata extraction failed", error=str(e))
                return {'page_count': 0}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract_metadata)