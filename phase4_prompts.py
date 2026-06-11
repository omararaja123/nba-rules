"""
Phase 4: RAG Prompt Templates
Production-quality prompts with guardrails against hallucination.
"""


class RAGPrompts:
    """Collection of RAG system prompts."""

    SYSTEM_PROMPT = """You are an expert NBA Rules Assistant. Your role is to answer questions about the NBA playing rules using ONLY the provided rulebook excerpts.

CRITICAL CONSTRAINTS:
1. Use ONLY information from the retrieved NBA rulebook excerpts provided.
2. Do NOT use outside knowledge, general basketball knowledge, or inferences beyond what is explicitly stated.
3. Do NOT invent rules, penalties, or procedures that are not in the excerpts.
4. ALWAYS cite your sources using the provided Rule, Section, and Page information.
5. If the retrieved excerpts do not contain enough information to answer the question, ALWAYS state: "I could not find enough information in the retrieved NBA rules sections to answer this question."

CITATION FORMAT:
- Use inline citations: "According to [Rule X, Section Y, p. Z], ..."
- Always include the rule number, section name, and page number.
- For multiple sources: "According to Rule 5, Section III (p. 16) and Rule 12, Section I (p. 40), ..."

ANSWER QUALITY:
- Be concise and direct.
- Provide complete answers when possible.
- Highlight specific numbers, percentages, or procedures.
- Clarify any conditions or exceptions mentioned in the rules.

ERROR HANDLING:
- If information is ambiguous in the excerpts, acknowledge the ambiguity.
- If you need clarification about what the question is asking, ask.
- Never make assumptions about missing information."""

    @staticmethod
    def create_user_prompt(question: str, context: str) -> str:
        """
        Create the user message for RAG.

        Args:
            question: User's question
            context: Retrieved context from rulebook

        Returns:
            Formatted user prompt
        """
        return f"""Question: {question}

{context}

Based ONLY on the retrieved NBA rulebook excerpts above, answer the question. Remember to cite all factual claims using Rule, Section, and Page information. If the excerpts do not contain enough information, state that clearly."""

    @staticmethod
    def create_evaluation_prompt(question: str, context: str, answer: str) -> str:
        """
        Create evaluation prompt for scoring answers.

        Args:
            question: User's question
            context: Retrieved context
            answer: Generated answer

        Returns:
            Evaluation prompt
        """
        return f"""Evaluate this RAG answer on faithfulness and relevance to the NBA rules question.

Question: {question}

Retrieved Context:
{context}

Generated Answer:
{answer}

Score this answer on two dimensions:

1. FAITHFULNESS (1-5):
   - 1 = Answer contains unsupported claims not in context
   - 2 = Some claims partially supported by context
   - 3 = Most claims supported, minor unsupported details
   - 4 = Fully supported by context, proper citations
   - 5 = Fully supported with strong, specific citations

2. RELEVANCE (1-5):
   - 1 = Does not address the question
   - 2 = Weakly related to question
   - 3 = Partially answers the question
   - 4 = Good answer to the question
   - 5 = Complete, thorough answer to the question

Provide:
- Faithfulness score (1-5)
- Relevance score (1-5)
- Brief explanation for each score
- Specific issues if present"""

    @staticmethod
    def create_citation_validation_prompt(answer: str, context: str) -> str:
        """
        Validate citations in answer against context.

        Args:
            answer: Generated answer
            context: Retrieved context

        Returns:
            Validation prompt
        """
        return f"""Check if all citations in this answer are accurate and support the claims made.

Answer:
{answer}

Retrieved Context:
{context}

For each citation in the answer:
1. Verify it appears in the retrieved context
2. Check if the cited passage actually supports the claim
3. Note any missing citations for factual claims
4. Flag any fabricated or inaccurate citations

Provide:
- Citation accuracy score (0-100%)
- List of issues found
- Recommendations for fixing citations"""


def get_system_prompt() -> str:
    """Get the system prompt for RAG."""
    return RAGPrompts.SYSTEM_PROMPT


def get_user_prompt(question: str, context: str) -> str:
    """Get the user prompt for a question."""
    return RAGPrompts.create_user_prompt(question, context)


def get_evaluation_prompt(question: str, context: str, answer: str) -> str:
    """Get the evaluation prompt."""
    return RAGPrompts.create_evaluation_prompt(question, context, answer)


def get_citation_validation_prompt(answer: str, context: str) -> str:
    """Get the citation validation prompt."""
    return RAGPrompts.create_citation_validation_prompt(answer, context)
