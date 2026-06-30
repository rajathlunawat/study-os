"""
StudyOS AI Service — LLM Client.

Responsibility: Provides a unified interface for sending prompts to an LLM
and receiving text responses.

Design Decision: This is intentionally a thin abstraction layer. The actual 
LLM backend is pluggable — it can be a local model (e.g., llama.cpp, Ollama), 
a cloud API (e.g., Google Gemini, OpenAI), or even a mock for testing. 
Swapping the backend only requires changing this file.

For the initial scaffold, we provide:
1. A placeholder/mock implementation for development without an LLM.
2. Clear integration points for adding a real backend.
"""

from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Abstraction layer over the LLM provider.

    Current implementation is a development placeholder that returns
    structured mock responses. Replace the `generate()` method body
    with an actual API call when ready.
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Args:
            model_name: Identifier for the LLM model to use.
                        e.g., "gemini-2.0-flash", "llama3", "gpt-4o-mini"
        """
        self.model_name = model_name or "placeholder"
        logger.info("LLMClient initialized with model: %s", self.model_name)

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Send a prompt to the LLM and return the text response.

        Args:
            prompt: The fully assembled prompt string (from PromptBuilder).
            max_tokens: Maximum number of tokens in the response.

        Returns:
            The raw text response from the LLM.

        Raises:
            ConnectionError: If the LLM API is unreachable.
            RuntimeError: If the LLM returns an error.
        """
        # ──────────────────────────────────────────────────────────────────
        # TODO: Replace this placeholder with a real LLM integration.
        #
        # Example integrations:
        #
        # --- Google Gemini ---
        # import google.generativeai as genai
        # genai.configure(api_key=settings.GEMINI_API_KEY)
        # model = genai.GenerativeModel(self.model_name)
        # response = model.generate_content(prompt)
        # return response.text
        #
        # --- Ollama (Local) ---
        # import requests
        # resp = requests.post("http://localhost:11434/api/generate", json={
        #     "model": self.model_name,
        #     "prompt": prompt,
        #     "stream": False
        # })
        # return resp.json()["response"]
        #
        # --- OpenAI ---
        # from openai import OpenAI
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # response = client.chat.completions.create(
        #     model=self.model_name,
        #     messages=[{"role": "user", "content": prompt}],
        #     max_tokens=max_tokens
        # )
        # return response.choices[0].message.content
        # ──────────────────────────────────────────────────────────────────

        logger.warning(
            "LLMClient is using PLACEHOLDER mode. "
            "No real LLM call is being made."
        )

        return self._placeholder_response(prompt)

    @staticmethod
    def _placeholder_response(prompt: str) -> str:
        """
        Return a mock response for development and testing.
        Detects the prompt type and returns appropriate structured output.
        """
        prompt_lower = prompt.lower()

        if "multiple-choice" in prompt_lower or "quiz" in prompt_lower:
            return (
                '[{"question": "What is the main topic discussed?", '
                '"options": ["Option A", "Option B", "Option C", "Option D"], '
                '"correct_answer": "Option A", '
                '"explanation": "Based on the context provided."}]'
            )

        if "flashcard" in prompt_lower:
            return (
                '[{"front": "What is a key concept?", '
                '"back": "A key concept is a fundamental idea from your notes."}]'
            )

        if "study plan" in prompt_lower:
            return (
                '[{"title": "Review fundamentals", '
                '"description": "Go through the core concepts.", '
                '"day_number": 1}]'
            )

        # Default: Q&A style
        return (
            "Based on the context from your notes [Chunk 1], "
            "the answer is: This is a placeholder response. "
            "Please connect a real LLM to get actual answers."
        )
