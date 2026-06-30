"""
StudyOS PYQ Service — Question Extractor.

Responsibility: Extracts individual questions from Previous Year Question (PYQ)
papers using pattern-based heuristics.

Design Decision: PYQ papers are notoriously messy, but usually follow numbered
patterns (e.g., "1. What is X?", "Q2(a). Define Y."). We use deterministic 
regex to split the document into distinct question blocks rather than using 
an LLM, saving tokens and ensuring predictable behavior.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractedQuestion:
    """
    A single question parsed from a PYQ paper.

    Attributes:
        number_label: The extracted question number (e.g., "1", "2(a)").
        text: The actual question text.
        marks: Optional extracted marks (e.g., "[5]" or "(10 Marks)").
    """
    number_label: str
    text: str
    marks: str | None = None


# ── Compiled Regex Patterns ───────────────────────────────────────────────────

# Matches standard question starts:
# "1. ", "Q1. ", "Question 1: ", "1(a). "
_QUESTION_START_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:Q(?:uestion)?\s*)?(\d+(?:[a-zA-Z]|\(\w+\))?)[\.\:\)]\s+',
    re.IGNORECASE
)

# Matches mark indicators usually found at the end of a line:
# "[5]", "(10 Marks)", "[5M]"
_MARKS_PATTERN = re.compile(
    r'\[\s*\d+\s*[mM]?(?:arks?)?\s*\]|\(\s*\d+\s*[mM]?(?:arks?)?\s*\)',
    re.IGNORECASE
)


def extract_questions(raw_text: str) -> List[ExtractedQuestion]:
    """
    Parse a raw PYQ paper text into discrete questions.

    Args:
        raw_text: Cleaned text from the uploaded PYQ PDF.

    Returns:
        A list of ExtractedQuestion objects.
    """
    if not raw_text or not raw_text.strip():
        return []

    questions = []
    
    # Find all matches for question starts
    matches = list(_QUESTION_START_PATTERN.finditer(raw_text))
    
    if not matches:
        return _fallback_heuristic(raw_text)

    for i, match in enumerate(matches):
        number_label = match.group(1).strip()
        
        # Get the text block for this question
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        
        block = raw_text[start_pos:end_pos].strip()
        
        # Attempt to extract marks from the block
        marks = None
        marks_match = list(_MARKS_PATTERN.finditer(block))
        if marks_match:
            # Use the last match as marks are usually at the end
            last_mark = marks_match[-1]
            marks = last_mark.group(0).strip()
            # Remove the marks from the question text itself
            block = block[:last_mark.start()].strip() + block[last_mark.end():].strip()
            
        # Clean up the question text (collapse excess whitespace)
        block = re.sub(r'\s+', ' ', block)
        
        if len(block) > 5:  # Ignore trivial/empty captures
            questions.append(ExtractedQuestion(
                number_label=number_label,
                text=block,
                marks=marks,
            ))

    return questions


def _fallback_heuristic(raw_text: str) -> List[ExtractedQuestion]:
    """
    Fallback if no standard 'Q1.' patterns are found.
    Treats each paragraph ending with a question mark as a question.
    """
    questions = []
    paragraphs = raw_text.split("\n\n")
    
    counter = 1
    for p in paragraphs:
        p = p.strip()
        if p.endswith("?"):
            p = re.sub(r'\s+', ' ', p)
            questions.append(ExtractedQuestion(
                number_label=str(counter),
                text=p,
            ))
            counter += 1
            
    return questions
