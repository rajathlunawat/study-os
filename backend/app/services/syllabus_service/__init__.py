"""
StudyOS Syllabus Service Public API.
"""

from .service import SyllabusService
from .topic_extractor import extract_topics, SyllabusTopic
from .mapper import TopicMapper

__all__ = [
    "SyllabusService",
    "extract_topics",
    "SyllabusTopic",
    "TopicMapper",
]
