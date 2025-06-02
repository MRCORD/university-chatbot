# =======================
# app/utils/text_chunking.py
# =======================
from typing import List, Dict, Any, Optional
import re

class TextChunker:
    """Enhanced text chunking strategies with metadata tracking."""

    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 page_boundaries: Optional[List[Dict[str, Any]]] = None):
        """Initialize TextChunker with configuration."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.page_boundaries = page_boundaries or []
        
        # Section patterns for title detection
        self.section_patterns = [
            r'^[A-ZÁÉÍÓÚÑ\s]{5,50}$',  # All caps titles
            r'^\d+\.\s+[A-Za-záéíóúñÁÉÍÓÚÑ][^.]{10,80}$',  # Numbered sections
            r'^[IVX]+\.\s+[A-Za-záéíóúñÁÉÍÓÚÑ][^.]{10,80}$',  # Roman numeral sections
            r'^Capítulo\s+\d+',  # Chapter titles
            r'^CAPÍTULO\s+[IVX\d]+',  # Chapter titles (caps)
        ]

    def chunk_by_sentences(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Chunk text by sentences with enhanced metadata tracking."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_with_space = sentence + " "
            
            if len(current_chunk) + len(sentence_with_space) <= self.chunk_size:
                current_chunk += sentence_with_space
            else:
                if current_chunk.strip():
                    # Calculate positions
                    chunk_text = current_chunk.strip()
                    chunk_end = current_start + len(chunk_text)
                    
                    # Create chunk with metadata
                    chunk_data = self._create_chunk_data(
                        document_id=document_id,
                        content=chunk_text,
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1
                
                # Start new chunk with overlap
                current_start = current_start + len(current_chunk) - self.chunk_overlap
                current_chunk = sentence_with_space
        
        # Add final chunk
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunk_end = current_start + len(chunk_text)
            
            chunk_data = self._create_chunk_data(
                document_id=document_id,
                content=chunk_text,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end
            )
            chunks.append(chunk_data)
        
        return chunks

    def chunk_by_paragraphs(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs with enhanced metadata tracking."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph_with_spacing = paragraph + "\n\n"
            
            if len(current_chunk) + len(paragraph_with_spacing) <= self.chunk_size:
                current_chunk += paragraph_with_spacing
            else:
                if current_chunk.strip():
                    # Calculate positions
                    chunk_text = current_chunk.strip()
                    chunk_end = current_start + len(chunk_text)
                    
                    # Create chunk with metadata
                    chunk_data = self._create_chunk_data(
                        document_id=document_id,
                        content=chunk_text,
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1
                
                # Start new chunk with overlap
                current_start = current_start + len(current_chunk) - self.chunk_overlap
                current_chunk = paragraph_with_spacing
        
        # Add final chunk
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunk_end = current_start + len(chunk_text)
            
            chunk_data = self._create_chunk_data(
                document_id=document_id,
                content=chunk_text,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end
            )
            chunks.append(chunk_data)
        
        return chunks

    def chunk_by_semantic_sections(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Chunk text by semantic sections (new method for better organization)."""
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        current_section_title = None
        
        for line in lines:
            # Check if this line is a section header
            section_title = self._extract_section_title_from_line(line)
            
            if section_title and current_chunk.strip():
                # Save current chunk before starting new section
                chunk_text = current_chunk.strip()
                chunk_end = current_start + len(chunk_text)
                
                chunk_data = self._create_chunk_data(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=chunk_end,
                    section_title=current_section_title
                )
                chunks.append(chunk_data)
                chunk_index += 1
                
                # Start new chunk
                current_start = chunk_end
                current_chunk = ""
                current_section_title = section_title
            
            # Add line to current chunk
            line_with_newline = line + "\n"
            if len(current_chunk) + len(line_with_newline) <= self.chunk_size:
                current_chunk += line_with_newline
            else:
                # Current chunk is full, save it
                if current_chunk.strip():
                    chunk_text = current_chunk.strip()
                    chunk_end = current_start + len(chunk_text)
                    
                    chunk_data = self._create_chunk_data(
                        document_id=document_id,
                        content=chunk_text,
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end,
                        section_title=current_section_title
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1
                
                # Start new chunk with overlap
                current_start = current_start + len(current_chunk) - self.chunk_overlap
                current_chunk = line_with_newline
        
        # Add final chunk
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunk_end = current_start + len(chunk_text)
            
            chunk_data = self._create_chunk_data(
                document_id=document_id,
                content=chunk_text,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end,
                section_title=current_section_title
            )
            chunks.append(chunk_data)
        
        return chunks

    def _create_chunk_data(self, 
                          document_id: str, 
                          content: str, 
                          chunk_index: int, 
                          start_char: int, 
                          end_char: int,
                          section_title: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized chunk data structure."""
        if section_title is None:
            section_title = self._extract_section_title(content)
        
        return {
            'document_id': document_id,
            'content': content,
            'chunk_index': chunk_index,
            'page_number': self._determine_page_number(start_char, end_char),
            'section_title': section_title,
            'start_char': start_char,
            'end_char': end_char,
            'character_count': len(content),
            'chunk_metadata': self._build_chunk_metadata(content, start_char, end_char)
        }

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
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        # Check first few lines for section patterns
        for i, line in enumerate(lines[:3]):  # Check first 3 lines
            title = self._extract_section_title_from_line(line)
            if title:
                return title
        
        return None

    def _extract_section_title_from_line(self, line: str) -> Optional[str]:
        """Extract section title from a single line."""
        line = line.strip()
        if not line:
            return None
        
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

    # Legacy methods for backward compatibility (now return simple strings)
    @staticmethod
    def chunk_by_sentences_simple(text: str, max_chunk_size: int = 1000) -> List[str]:
        """Legacy method: Chunk text by sentences, returning simple string chunks."""
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
    def chunk_by_paragraphs_simple(text: str, max_chunk_size: int = 1000) -> List[str]:
        """Legacy method: Chunk text by paragraphs, returning simple string chunks."""
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
