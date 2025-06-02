# =======================
# app/utils/document_processing.py
# =======================
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import structlog
from pathlib import Path
import pypdf

# Import the enhanced TextChunker for alternative chunking strategies
from app.utils.text_chunking import TextChunker

logger = structlog.get_logger()


class DocumentProcessor:
    """PDF processing utilities for document extraction and chunking."""
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 chunking_strategy: str = "default"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy  # "default", "sentences", "paragraphs", "semantic"
        # Store page boundary information for better tracking
        self.page_boundaries = []
        self.section_patterns = [
            r'^[A-ZÁÉÍÓÚÑ\s]{5,50}$',  # All caps titles
            r'^\d+\.\s+[A-Za-záéíóúñÁÉÍÓÚÑ][^.]{10,80}$',  # Numbered sections
            r'^[IVX]+\.\s+[A-Za-záéíóúñÁÉÍÓÚÑ][^.]{10,80}$',  # Roman numeral sections
            r'^Capítulo\s+\d+',  # Chapter titles
            r'^CAPÍTULO\s+[IVX\d]+',  # Chapter titles (caps)
        ]
    
    async def process_pdf(self, file_path: str, document_id: str) -> List[Dict[str, Any]]:
        """Process PDF file: extract text and create chunks."""
        try:
            # Extract text from PDF with page tracking
            text, page_info = await self._extract_pdf_text(file_path)
            
            if not text.strip():
                logger.warning("No text extracted from PDF", document_id=document_id)
                return []
            
            # Store page boundaries for character position mapping
            self.page_boundaries = page_info
            
            # Create chunks with enhanced metadata
            chunks = await self._chunk_text(text, document_id)
            
            logger.info("PDF processed successfully", 
                       document_id=document_id, 
                       chunks_created=len(chunks),
                       text_length=len(text),
                       pages_processed=len(page_info))
            
            return chunks
            
        except Exception as e:
            logger.error("PDF processing failed", 
                        document_id=document_id, 
                        error=str(e))
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract text from PDF file using pypdf, preserving page boundaries."""
        if not pypdf:
            raise ImportError("pypdf not available. Install with: pip install pypdf")
        
        def _extract():
            try:
                with open(file_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    text_parts = []
                    page_info = []
                    current_position = 0
                    
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                # Store page boundary information
                                page_start = current_position
                                page_end = current_position + len(page_text)
                                
                                page_info.append({
                                    'page_number': page_num + 1,
                                    'start_char': page_start,
                                    'end_char': page_end,
                                    'text_length': len(page_text)
                                })
                                
                                text_parts.append(page_text)
                                current_position = page_end + 1  # +1 for the newline we'll add
                                
                        except Exception as e:
                            logger.warning("Failed to extract text from page", 
                                         page=page_num, error=str(e))
                            continue
                    
                    # Join with newlines to preserve page boundaries
                    full_text = "\n".join(text_parts)
                    return full_text, page_info
                    
            except Exception as e:
                logger.error("PDF text extraction failed", file_path=file_path, error=str(e))
                raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract)
    
    async def _chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks for embeddings with enhanced metadata."""
        if not text.strip():
            return []
        
        # Use alternative chunking strategies if specified
        if self.chunking_strategy != "default":
            return await self._chunk_text_with_strategy(text, document_id)
        
        # Default chunking strategy (existing implementation)
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
            
            if chunk_text and len(chunk_text) > 50:  # Only include substantial chunks
                # Determine page number based on character position
                page_number = self._determine_page_number(start, end)
                
                # Extract section title if present
                section_title = self._extract_section_title(chunk_text)
                
                # Build chunk metadata
                chunk_metadata = self._build_chunk_metadata(chunk_text, start, end)
                
                chunks.append({
                    'document_id': document_id,
                    'content': chunk_text,
                    'chunk_index': chunk_index,
                    'page_number': page_number,
                    'section_title': section_title,
                    'start_char': start,
                    'end_char': end,
                    'character_count': len(chunk_text),
                    'chunk_metadata': chunk_metadata
                })
                chunk_index += 1
            
            # Move to next chunk with overlap
            start = max(end - self.chunk_overlap, start + 1)
            
            # Safety check to prevent infinite loop
            if start >= len(text):
                break
        
        return chunks

    async def _chunk_text_with_strategy(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Use alternative chunking strategies via TextChunker."""
        chunker = TextChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            page_boundaries=self.page_boundaries
        )
        
        if self.chunking_strategy == "sentences":
            return chunker.chunk_by_sentences(text, document_id)
        elif self.chunking_strategy == "paragraphs":
            return chunker.chunk_by_paragraphs(text, document_id)
        elif self.chunking_strategy == "semantic":
            return chunker.chunk_by_semantic_sections(text, document_id)
        else:
            # Fallback to default strategy
            return await self._chunk_text(text, document_id)
    
    def _determine_page_number(self, start_char: int, end_char: int) -> Optional[int]:
        """Determine page number based on character positions."""
        if not self.page_boundaries:
            return None
        
        # Find which page contains the majority of this chunk
        chunk_midpoint = (start_char + end_char) // 2
        
        for page_info in self.page_boundaries:
            if page_info['start_char'] <= chunk_midpoint <= page_info['end_char']:
                return page_info['page_number']
        
        # Fallback: find the page with most overlap
        max_overlap = 0
        best_page = None
        
        for page_info in self.page_boundaries:
            overlap_start = max(start_char, page_info['start_char'])
            overlap_end = min(end_char, page_info['end_char'])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_page = page_info['page_number']
        
        return best_page
    
    def _extract_section_title(self, text: str) -> Optional[str]:
        """Extract section title from chunk text using pattern matching."""
        import re
        
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        # Check first few lines for section patterns
        for i, line in enumerate(lines[:3]):  # Check first 3 lines
            line = line.strip()
            if not line:
                continue
                
            # Check against section patterns
            for pattern in self.section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    # Clean up the title
                    title = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering
                    title = re.sub(r'^[IVX]+\.\s*', '', title)  # Remove roman numerals
                    title = title.strip()
                    
                    if len(title) > 5:  # Ensure it's substantial
                        return title
        
        return None
    
    def _build_chunk_metadata(self, text: str, start_char: int, end_char: int) -> Dict[str, Any]:
        """Build metadata for a text chunk."""
        import re
        
        metadata = {
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_headings': False,
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'contains_formulas': bool(re.search(r'[=+\-*/]\s*\d+', text)),
            'language_indicators': []
        }
        
        # Check for heading indicators
        lines = text.split('\n')
        for line in lines[:5]:  # Check first few lines
            line = line.strip()
            if line.isupper() and len(line) > 5:
                metadata['has_headings'] = True
                break
            if re.match(r'^\d+\.\s+[A-Z]', line):
                metadata['has_headings'] = True
                break
        
        # Detect language indicators
        if re.search(r'\b(artículo|capítulo|sección|página)\b', text, re.IGNORECASE):
            metadata['language_indicators'].append('spanish')
        if re.search(r'\b(article|chapter|section|page)\b', text, re.IGNORECASE):
            metadata['language_indicators'].append('english')
        
        return metadata
    
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