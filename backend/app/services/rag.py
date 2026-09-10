import time
import logging
from typing import List, Optional, Tuple
from app.schemas.chat import ChatResponse, SourceReference
from app.services.retrieval import retrieval_service, RetrievedChunk
from app.services.llm import get_llm_provider, LLMProvider, MockLLMProvider

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are an enterprise document question-answering assistant.
You must answer ONLY using the supplied context.
Do not use outside knowledge.
If the context does not contain enough information to answer the question, say that the information is not available in the approved knowledge base.
Do not invent facts, sources, pages, numbers, policies, or names.
Keep answers concise, professional, accurate, and directly grounded in the provided excerpts."""

UNSUPPORTED_FALLBACK_TEXT = "I couldn't find sufficient information in the approved knowledge base to answer this question."

QUOTA_EXHAUSTED_FALLBACK_TEXT = "The AI generation service is temporarily unavailable. The relevant source documents were retrieved successfully. Please try again later."


class RAGService:
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self._llm_provider = llm_provider
        self._mock_fallback_provider: Optional[MockLLMProvider] = None

    @property
    def llm_provider(self) -> LLMProvider:
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider()
        return self._llm_provider

    @property
    def mock_fallback_provider(self) -> MockLLMProvider:
        if self._mock_fallback_provider is None:
            self._mock_fallback_provider = MockLLMProvider()
        return self._mock_fallback_provider

    async def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[ChatResponse, float]:
        """
        Execute full RAG pipeline:
        1. Retrieval of relevant chunks.
        2. Strict relevance/grounding verification.
        3. Prompt synthesis with explicit context citations.
        4. LLM inference with safe demo fallback on quota exhaustion.
        5. Grounding check on generated answer.
        6. Source metadata compilation.
        """
        start_time = time.time()
        clean_question = question.strip()

        # Step 1: Retrieval
        relevant_chunks: List[RetrievedChunk] = retrieval_service.retrieve_relevant_chunks(
            question=clean_question,
            top_k=top_k,
            threshold=similarity_threshold
        )

        # Step 2: Grounding check before LLM
        if not relevant_chunks:
            logger.info(f"No relevant chunks passed threshold for question: '{clean_question}'")
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return ChatResponse(
                answer=UNSUPPORTED_FALLBACK_TEXT,
                has_answer=False,
                sources=[],
                provider="gemini"
            ), latency_ms

        # Step 3: Construct Grounded Prompt
        context_blocks: List[str] = []
        sources: List[SourceReference] = []

        for idx, chunk in enumerate(relevant_chunks, 1):
            source_header = (
                f"[Source {idx}] Document: {chunk.filename} | "
                f"Page: {chunk.page_number} | "
                f"Section: {chunk.section}"
            )
            context_blocks.append(f"{source_header}\n{chunk.text}")

            sources.append(SourceReference(
                document=chunk.filename,
                document_id=chunk.document_id,
                page=chunk.page_number,
                section=chunk.section,
                chunk_id=chunk.chunk_id,
                supporting_text=chunk.text,
                relevance_score=chunk.similarity_score
            ))

        formatted_context = "\n\n".join(context_blocks)
        prompt = (
            f"Approved Knowledge Base Context:\n"
            f"{formatted_context}\n\n"
            f"Question:\n"
            f"{clean_question}\n\n"
            f"Answer:"
        )

        # Step 4: LLM Generation with Controlled Demo Fallback
        provider_name = getattr(self.llm_provider, "__class__", type(self.llm_provider)).__name__
        is_fallback = False

        try:
            generated_answer = await self.llm_provider.generate_response(
                prompt=prompt,
                system_prompt=SYSTEM_INSTRUCTION
            )
        except Exception as e:
            err_str = str(e)
            logger.error(f"Error during LLM generation: {e}", exc_info=True)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Detect Gemini 429 / RESOURCE_EXHAUSTED / quota exhaustion
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                logger.warning(
                    "[RAG SAFE FALLBACK] Gemini quota exhausted (429 RESOURCE_EXHAUSTED). "
                    "Engaging MockLLMProvider controlled demo fallback against retrieved context."
                )
                try:
                    generated_answer = await self.mock_fallback_provider.generate_response(
                        prompt=prompt,
                        system_prompt=SYSTEM_INSTRUCTION
                    )
                    is_fallback = True
                except Exception as fallback_err:
                    logger.error(f"Fallback generation error: {fallback_err}", exc_info=True)
                    return ChatResponse(
                        answer=QUOTA_EXHAUSTED_FALLBACK_TEXT,
                        has_answer=False,
                        sources=sources,
                        provider="controlled_demo_fallback"
                    ), latency_ms
            else:
                # Generic fallback for any other generation errors
                return ChatResponse(
                    answer="The AI generation service is temporarily unavailable. Please try again later.",
                    has_answer=False,
                    sources=sources,
                    provider=provider_name
                ), latency_ms

        # Step 5: Post-generation Grounding Check
        lower_answer = generated_answer.lower()
        unsupported_phrases = [
            "not available in the approved knowledge base",
            "couldn't find sufficient information",
            "could not find sufficient information",
            "does not contain enough information",
            "not mentioned in the provided",
            "no information provided",
            "insufficient information",
            "cannot be answered from the provided",
            "provided context does not contain",
            "does not contain information",
            "not specified in the",
            "not available in the company",
            "not mentioned in the approved",
            "unable to find"
        ]

        is_unsupported = any(phrase in lower_answer for phrase in unsupported_phrases)

        if is_unsupported:
            final_answer = UNSUPPORTED_FALLBACK_TEXT
            has_answer = False
            final_sources = []
        else:
            final_answer = generated_answer
            has_answer = True
            final_sources = sources

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return ChatResponse(
            answer=final_answer,
            has_answer=has_answer,
            sources=final_sources,
            provider="controlled_demo_fallback" if is_fallback else provider_name
        ), latency_ms


rag_service = RAGService()
