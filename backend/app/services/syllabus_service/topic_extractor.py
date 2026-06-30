"""
StudyOS Syllabus Service — Topic Extractor.

Responsibility: Extracts a structured list of topics, units, and modules
from raw syllabus text using pattern-based heuristics.

Design Decision: We use deterministic regex/heuristic parsing first,
falling back to AI extraction only when patterns fail. This keeps the
system fast, reproducible, and avoids burning LLM tokens on structured
documents that typically follow predictable formats.

Common syllabus patterns recognized:
- "Unit 1: Introduction to ..."
- "Module 3 - Data Structures"
- "Chapter IV: ..."
- Numbered lists: "1. Topic Name", "1.1 Sub-topic"
- Bulleted lists with topic-like structure
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SyllabusTopic:
    """
    A single topic or unit extracted from a syllabus.

    Attributes:
        title: The name of the topic or unit.
        unit_number: The extracted unit/module/chapter number (if found).
        subtopics: List of sub-topics or bullet points under this unit.
        raw_text: The original text block this topic was extracted from.
    """
    title: str
    unit_number: Optional[int] = None
    subtopics: List[str] = field(default_factory=list)
    raw_text: str = ""


# ── Compiled Regex Patterns ───────────────────────────────────────────────────

# Matches: "Unit 1: Topic", "Unit I - Topic", "UNIT 1 Topic"
_UNIT_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:unit|module|chapter)\s+'
    r'(?:(\d+)|([IVXLC]+))\s*[:\-–—.\s]\s*(.+)',
    re.IGNORECASE
)

# Matches: "1. Topic Name" or "1) Topic Name" (top-level numbered items)
_NUMBERED_PATTERN = re.compile(
    r'(?:^|\n)\s*(\d+)\s*[.)]\s+(.+)',
)

# Matches: "1.1 Sub-topic" or "2.3. Sub-topic"
_SUB_NUMBERED_PATTERN = re.compile(
    r'(?:^|\n)\s*\d+\.\d+\.?\s+(.+)',
)

# Roman numeral lookup for conversion
_ROMAN_MAP = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
              "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def extract_topics(text: str) -> List[SyllabusTopic]:
    """
    Extract structured topics from raw syllabus text.

    Tries unit/module/chapter patterns first. If none are found,
    falls back to numbered list extraction.

    Args:
        text: The cleaned text of a syllabus document.

    Returns:
        A list of SyllabusTopic objects in document order.
    """
    if not text or not text.strip():
        return []

    # Strategy 1: Unit/Module/Chapter headers
    topics = _extract_unit_headers(text)
    if topics:
        return topics

    # Strategy 2: Top-level numbered list
    topics = _extract_numbered_list(text)
    if topics:
        return topics

    # Strategy 3: Line-by-line heuristic for unstructured syllabi
    topics = _extract_line_heuristic(text)
    return topics


# ── Extraction Strategies ─────────────────────────────────────────────────────

def _extract_unit_headers(text: str) -> List[SyllabusTopic]:
    """
    Extract topics using Unit/Module/Chapter header patterns.
    Also captures sub-topics between consecutive headers.
    """
    matches = list(_UNIT_PATTERN.finditer(text))
    if not matches:
        return []

    topics = []
    for i, match in enumerate(matches):
        # Parse the unit number (Arabic or Roman)
        arabic_num = match.group(1)
        roman_num = match.group(2)
        title = match.group(3).strip()

        unit_number = None
        if arabic_num:
            unit_number = int(arabic_num)
        elif roman_num:
            unit_number = _ROMAN_MAP.get(roman_num.upper())

        # Extract the text block between this header and the next
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[start_pos:end_pos].strip()

        # Extract sub-topics from the block
        subtopics = _extract_subtopics(block_text)

        topics.append(SyllabusTopic(
            title=title,
            unit_number=unit_number,
            subtopics=subtopics,
            raw_text=block_text,
        ))

    return topics


def _extract_numbered_list(text: str) -> List[SyllabusTopic]:
    """
    Extract topics from a simple numbered list (1. Topic, 2. Topic, ...).
    """
    matches = list(_NUMBERED_PATTERN.finditer(text))
    if len(matches) < 2:
        # Need at least 2 numbered items to consider this a valid list
        return []

    topics = []
    for i, match in enumerate(matches):
        num = int(match.group(1))
        title = match.group(2).strip()

        # Get sub-content between this item and the next
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[start_pos:end_pos].strip()

        subtopics = _extract_subtopics(block_text)

        topics.append(SyllabusTopic(
            title=title,
            unit_number=num,
            subtopics=subtopics,
            raw_text=block_text,
        ))

    return topics


def _extract_line_heuristic(text: str) -> List[SyllabusTopic]:
    """
    Last resort: treat each non-empty, non-trivial line as a potential topic.
    Filters out lines that are too short or look like metadata.
    """
    topics = []
    for line in text.splitlines():
        line = line.strip()
        # Skip empty, very short, or metadata-like lines
        if len(line) < 5:
            continue
        if line.lower().startswith(("page", "date", "semester", "credit", "total")):
            continue

        topics.append(SyllabusTopic(
            title=line,
            raw_text=line,
        ))

    return topics


def _extract_subtopics(block: str) -> List[str]:
    """
    Extract sub-topics from a text block using sub-numbered patterns
    or short bullet-like lines.
    """
    subtopics = []

    # Try sub-numbered patterns first (1.1, 1.2, etc.)
    sub_matches = _SUB_NUMBERED_PATTERN.findall(block)
    if sub_matches:
        return [s.strip() for s in sub_matches if s.strip()]

    # Fall back to short lines that look like bullet points
    for line in block.splitlines():
        line = line.strip().lstrip("•-–—*● ")
        if 5 <= len(line) <= 200:
            subtopics.append(line)

    return subtopics
