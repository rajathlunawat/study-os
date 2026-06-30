"""
StudyOS AI Service — Prompt Builder.

Responsibility: Constructs structured prompts for the LLM.
Combines system instructions, retrieved RAG context, and the user's query
into a well-formatted prompt string.

Design Decision: Prompts are built as plain strings rather than using a 
templating engine (e.g., Jinja2). This keeps the dependency footprint zero 
and makes prompts easily auditable in source control.
"""

from typing import List


class PromptBuilder:
    """
    Constructs domain-specific prompts for different StudyOS features.
    """

    # ── System Personas ───────────────────────────────────────────────────────

    SYSTEM_QA = (
        "You are StudyOS, an AI study assistant. "
        "Answer the student's question using ONLY the provided context. "
        "If the context does not contain enough information, say: "
        "'I don't have enough information in your notes to answer this.' "
        "Never answer from general knowledge. Always cite which chunk(s) you used."
    )

    SYSTEM_QUIZ = (
        "You are StudyOS Quiz Generator. "
        "Generate multiple-choice questions based ONLY on the provided context. "
        "Each question must have exactly 4 options labeled A, B, C, D. "
        "Provide the correct answer and a brief explanation. "
        "Output valid JSON as an array of objects with keys: "
        "'question', 'options' (list of 4 strings), 'correct_answer', 'explanation'."
    )

    SYSTEM_FLASHCARD = (
        "You are StudyOS Flashcard Generator. "
        "Create concise flashcards based ONLY on the provided context. "
        "Each flashcard should have a clear 'front' (question/term) and "
        "'back' (answer/definition). "
        "Output valid JSON as an array of objects with keys: 'front', 'back'."
    )

    SYSTEM_STUDY_PLAN = (
        "You are StudyOS Study Planner. "
        "Create a structured study plan based on the provided context. "
        "Break the material into logical daily tasks. "
        "Output valid JSON as an array of objects with keys: "
        "'title', 'description', 'day_number'."
    )

    # ── Prompt Assembly ───────────────────────────────────────────────────────

    @staticmethod
    def build_qa_prompt(query: str, context_chunks: List[str]) -> str:
        """
        Build a RAG prompt for question-answering.

        Args:
            query: The student's question.
            context_chunks: List of text chunks retrieved from FAISS.

        Returns:
            A fully assembled prompt string.
        """
        context_block = PromptBuilder._format_context(context_chunks)
        return (
            f"{PromptBuilder.SYSTEM_QA}\n\n"
            f"--- CONTEXT FROM YOUR NOTES ---\n"
            f"{context_block}\n"
            f"--- END CONTEXT ---\n\n"
            f"Student's Question: {query}\n\n"
            f"Answer:"
        )

    @staticmethod
    def build_quiz_prompt(context_chunks: List[str], num_questions: int = 5) -> str:
        """
        Build a prompt to generate quiz questions from context.
        """
        context_block = PromptBuilder._format_context(context_chunks)
        return (
            f"{PromptBuilder.SYSTEM_QUIZ}\n\n"
            f"--- CONTEXT ---\n"
            f"{context_block}\n"
            f"--- END CONTEXT ---\n\n"
            f"Generate exactly {num_questions} multiple-choice questions.\n"
            f"Output ONLY valid JSON, no other text."
        )

    @staticmethod
    def build_flashcard_prompt(context_chunks: List[str], num_cards: int = 10) -> str:
        """
        Build a prompt to generate flashcards from context.
        """
        context_block = PromptBuilder._format_context(context_chunks)
        return (
            f"{PromptBuilder.SYSTEM_FLASHCARD}\n\n"
            f"--- CONTEXT ---\n"
            f"{context_block}\n"
            f"--- END CONTEXT ---\n\n"
            f"Generate exactly {num_cards} flashcards.\n"
            f"Output ONLY valid JSON, no other text."
        )

    @staticmethod
    def build_study_plan_prompt(
        topic: str, 
        context_chunks: List[str], 
        num_days: int = 7
    ) -> str:
        """
        Build a prompt to generate a study schedule.
        """
        context_block = PromptBuilder._format_context(context_chunks)
        return (
            f"{PromptBuilder.SYSTEM_STUDY_PLAN}\n\n"
            f"--- CONTEXT ---\n"
            f"{context_block}\n"
            f"--- END CONTEXT ---\n\n"
            f"Topic: {topic}\n"
            f"Create a study plan spanning {num_days} days.\n"
            f"Output ONLY valid JSON, no other text."
        )

    # ── Internal Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _format_context(chunks: List[str]) -> str:
        """
        Format a list of retrieved text chunks into a numbered context block.
        Numbering allows the LLM to cite specific chunks in its answer.
        """
        if not chunks:
            return "(No context available)"

        formatted_parts = []
        for i, chunk in enumerate(chunks, start=1):
            formatted_parts.append(f"[Chunk {i}]\n{chunk}")

        return "\n\n".join(formatted_parts)
