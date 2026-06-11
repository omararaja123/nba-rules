"""
Answer generation module for NBA Rules RAG system
Uses Claude to generate grounded answers based on retrieved context
"""

import os
from anthropic import Anthropic
from config import LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE


class AnswerGenerator:
    """Generates answers using Claude based on retrieved context."""

    def __init__(self):
        """Initialize the Claude client."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it in your .env file or environment."
            )

        self.client = Anthropic(api_key=api_key)
        self.conversation_history = []

    def system_prompt(self) -> str:
        """Return the system prompt for the RAG chatbot."""
        return """You are an expert NBA rules official answering questions about the Official 2025–26 NBA Playing Rules.

You have access to the official NBA rulebook content provided below.

**Instructions:**
1. Answer ONLY based on the provided rulebook excerpts
2. Be accurate, concise, and professional
3. Include specific rule numbers and section titles in your answer (e.g., "Rule 4, Section I")
4. If the answer requires information not in the provided rulebook, clearly state: "This information is not available in the official NBA rulebook provided."
5. For questions about penalties or specific scenarios, cite the exact rule
6. Use simple, clear language suitable for someone unfamiliar with basketball

**Important:** Your answer must be grounded entirely in the provided rulebook content. Do not use external knowledge about NBA rules."""

    def generate_answer(self, question: str, context: str, retrieved_chunks: list) -> dict:
        """
        Generate an answer using Claude based on retrieved context.

        Args:
            question: User's question
            context: Formatted context from retriever
            retrieved_chunks: List of retrieved chunk dicts for citations

        Returns:
            Dict with answer text, citations, and metadata
        """
        # Build the user message with context
        user_message = f"""Rulebook Context:
{context}

---

Question: {question}

Please answer the question based ONLY on the rulebook content provided above."""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                system=self.system_prompt(),
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            answer_text = response.content[0].text

            # Format citations
            citations = self._extract_citations(retrieved_chunks)

            return {
                'answer': answer_text,
                'citations': citations,
                'chunks_used': len(retrieved_chunks),
                'success': True,
                'error': None
            }

        except Exception as e:
            return {
                'answer': f"Error generating answer: {str(e)}",
                'citations': [],
                'chunks_used': 0,
                'success': False,
                'error': str(e)
            }

    def _extract_citations(self, retrieved_chunks: list) -> list:
        """
        Extract citation information from retrieved chunks.

        Args:
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            List of citation dicts
        """
        citations = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            citation = {
                'source_number': i,
                'rule_number': chunk['rule_number'],
                'rule_title': chunk['rule_title'],
                'section': chunk['section_title'],
                'page': chunk['page_number'],
                'citation_text': f"Rule {chunk['rule_number']}: {chunk['rule_title']} ({chunk['section_title']}, Page {chunk['page_number']})"
            }
            citations.append(citation)
        return citations

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

    def format_answer_with_citations(self, answer: dict) -> str:
        """
        Format answer with inline citations.

        Args:
            answer: Answer dict from generate_answer()

        Returns:
            Formatted answer string with citations
        """
        if not answer['success']:
            return answer['answer']

        formatted = answer['answer']

        if answer['citations']:
            formatted += "\n\n**Sources:**\n"
            for citation in answer['citations']:
                formatted += (
                    f"- [{citation['source_number']}] "
                    f"Rule {citation['rule_number']}: {citation['rule_title']} "
                    f"({citation['section']}, Page {citation['page']})\n"
                )

        return formatted
