"""
StudyOS AI Service — Response Parser.

Responsibility: Parses and validates JSON responses from the LLM.
Handles the fragile boundary between free-form LLM text and structured
application data.

Design Decision: We attempt multiple JSON extraction strategies (direct parse,
code-block extraction, brace extraction) to maximize robustness against
different LLM output formats.
"""

import json
import re
from typing import Any, Dict, List

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ResponseParser:
    """
    Extracts and validates structured JSON from raw LLM output.
    """

    @staticmethod
    def parse_json_response(raw_text: str) -> List[Dict[str, Any]]:
        """
        Attempt to extract a JSON array from raw LLM output.

        Tries multiple strategies in order:
        1. Direct JSON parse of the entire string.
        2. Extract from markdown code blocks (```json ... ```).
        3. Find the first JSON array using bracket matching.

        Args:
            raw_text: The raw string returned by the LLM.

        Returns:
            A list of dictionaries parsed from the JSON.

        Raises:
            ValueError: If no valid JSON array can be extracted.
        """
        if not raw_text or not raw_text.strip():
            raise ValueError("LLM returned an empty response.")

        # Strategy 1: Direct parse
        parsed = ResponseParser._try_direct_parse(raw_text)
        if parsed is not None:
            return parsed

        # Strategy 2: Extract from markdown code block
        parsed = ResponseParser._try_code_block_extraction(raw_text)
        if parsed is not None:
            return parsed

        # Strategy 3: Find the first JSON array with bracket matching
        parsed = ResponseParser._try_bracket_extraction(raw_text)
        if parsed is not None:
            return parsed

        logger.warning("Failed to parse JSON from LLM response: %s", raw_text[:200])
        raise ValueError("Could not extract valid JSON from the AI response.")

    # ── Extraction Strategies ─────────────────────────────────────────────────

    @staticmethod
    def _try_direct_parse(text: str) -> List[Dict[str, Any]] | None:
        """Attempt to parse the entire string as JSON."""
        try:
            result = json.loads(text.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        return None

    @staticmethod
    def _try_code_block_extraction(text: str) -> List[Dict[str, Any]] | None:
        """Extract JSON from a ```json ... ``` code block."""
        # Matches both ```json and ``` code blocks
        pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _try_bracket_extraction(text: str) -> List[Dict[str, Any]] | None:
        """Find and parse the first JSON array in the text using bracket matching."""
        start = text.find('[')
        if start == -1:
            return None

        # Find the matching closing bracket
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '[':
                depth += 1
            elif text[i] == ']':
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(text[start:i + 1])
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        pass
                    break
        return None
