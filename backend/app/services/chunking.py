import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.utils.file_parser import ExtractedDocument, ExtractedBlock
from app.core.config import settings


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    page_number: Optional[int]
    section: Optional[str]
    word_count: int
    metadata: Dict[str, Any]


class ChunkingService:
    def __init__(
        self,
        target_words: int = settings.CHUNK_TARGET_WORDS,
        overlap_words: int = settings.CHUNK_OVERLAP_WORDS,
    ):
        self.target_words = target_words
        self.overlap_words = overlap_words

    def chunk_document(self, doc: ExtractedDocument, document_id: str) -> List[DocumentChunk]:
        """
        Split extracted document blocks into chunks of target size with word overlap.
        Preserves paragraph boundaries and metadata.
        """
        chunks: List[DocumentChunk] = []

        if not doc.blocks:
            # Handle empty document
            if doc.raw_text.strip():
                # Fallback if blocks were not generated
                raw_words = doc.raw_text.split()
                if raw_words:
                    chunks.extend(self._chunk_words(
                        words=raw_words,
                        document_id=document_id,
                        filename=doc.filename,
                        page_number=1,
                        section="General"
                    ))
            return chunks

        # Process blocks grouped by page/section or accumulated into target word sizes
        current_blocks: List[str] = []
        current_word_count: int = 0
        current_page: Optional[int] = doc.blocks[0].page_number if doc.blocks else 1
        current_section: Optional[str] = doc.blocks[0].section if doc.blocks else "General"

        for block in doc.blocks:
            block_text = block.text.strip()
            if not block_text:
                continue

            block_words = block_text.split()
            block_word_count = len(block_words)

            # If a single block is already larger than target_words, split it internally
            if block_word_count > self.target_words:
                # First flush accumulated blocks if any
                if current_blocks:
                    chunk = self._create_chunk_from_text(
                        text="\n\n".join(current_blocks),
                        word_count=current_word_count,
                        document_id=document_id,
                        filename=doc.filename,
                        page_number=current_page,
                        section=current_section
                    )
                    chunks.append(chunk)
                    current_blocks = []
                    current_word_count = 0

                # Subdivide the large block with overlap
                sub_chunks = self._chunk_words(
                    words=block_words,
                    document_id=document_id,
                    filename=doc.filename,
                    page_number=block.page_number,
                    section=block.section
                )
                chunks.extend(sub_chunks)
                continue

            # If adding this block exceeds target words, create chunk
            if current_word_count + block_word_count > self.target_words and current_blocks:
                chunk = self._create_chunk_from_text(
                    text="\n\n".join(current_blocks),
                    word_count=current_word_count,
                    document_id=document_id,
                    filename=doc.filename,
                    page_number=current_page,
                    section=current_section
                )
                chunks.append(chunk)

                current_blocks = [block_text]
                current_word_count = block_word_count
                current_page = block.page_number
                current_section = block.section
            else:
                if not current_blocks:
                    current_page = block.page_number
                    current_section = block.section
                current_blocks.append(block_text)
                current_word_count += block_word_count

        # Final remaining blocks
        if current_blocks:
            chunk = self._create_chunk_from_text(
                text="\n\n".join(current_blocks),
                word_count=current_word_count,
                document_id=document_id,
                filename=doc.filename,
                page_number=current_page,
                section=current_section
            )
            chunks.append(chunk)

        return chunks

    def _chunk_words(
        self,
        words: List[str],
        document_id: str,
        filename: str,
        page_number: Optional[int],
        section: Optional[str]
    ) -> List[DocumentChunk]:
        """Helper to break a list of words into overlapping chunks."""
        result: List[DocumentChunk] = []
        step = max(1, self.target_words - self.overlap_words)
        
        for i in range(0, len(words), step):
            window = words[i : i + self.target_words]
            if not window:
                continue
            chunk = self._create_chunk(
                words=window,
                document_id=document_id,
                filename=filename,
                page_number=page_number,
                section=section
            )
            result.append(chunk)
            if i + self.target_words >= len(words):
                break

        return result

    def _create_chunk(
        self,
        words: List[str],
        document_id: str,
        filename: str,
        page_number: Optional[int],
        section: Optional[str]
    ) -> DocumentChunk:
        return self._create_chunk_from_text(
            text=" ".join(words),
            word_count=len(words),
            document_id=document_id,
            filename=filename,
            page_number=page_number,
            section=section
        )

    def _create_chunk_from_text(
        self,
        text: str,
        word_count: int,
        document_id: str,
        filename: str,
        page_number: Optional[int],
        section: Optional[str]
    ) -> DocumentChunk:
        chunk_id = f"doc_{document_id}_chunk_{uuid.uuid4().hex[:8]}"
        
        metadata = {
            "document_id": str(document_id),
            "filename": str(filename),
            "page_number": int(page_number) if page_number is not None else 1,
            "section": str(section) if section else "General",
            "chunk_id": chunk_id,
            "word_count": int(word_count)
        }

        return DocumentChunk(
            chunk_id=chunk_id,
            document_id=str(document_id),
            filename=str(filename),
            text=text,
            page_number=metadata["page_number"],
            section=metadata["section"],
            word_count=int(word_count),
            metadata=metadata
        )


chunking_service = ChunkingService()
