"""
StudyOS Prompts — Template Loader.

Responsibility: Loads, caches, and formats text-based prompt templates from disk.

Design Decision: Reading files from disk on every API call is slow. This loader 
reads the .txt templates once on startup and caches them in memory. It uses 
standard Python string formatting (.format) to inject variables like {context}.
"""

from pathlib import Path
from typing import Dict, Any

from app.core.exceptions import StudyOSException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PromptLoader:
    """
    Singleton class to manage and format LLM prompt templates.
    """
    _cache: Dict[str, str] = {}
    
    # Resolve the absolute path to the prompts directory
    _prompts_dir = Path(__file__).parent.resolve()

    @classmethod
    def get_template(cls, template_name: str) -> str:
        """
        Load a prompt template from disk, returning it from cache if available.
        
        Args:
            template_name: The base name of the file (e.g., "quiz").
            
        Returns:
            The raw string content of the template.
            
        Raises:
            StudyOSException: If the file does not exist.
        """
        filename = f"{template_name}.txt"
        
        if filename in cls._cache:
            return cls._cache[filename]

        file_path = cls._prompts_dir / filename
        
        if not file_path.exists():
            raise StudyOSException(
                message=f"Prompt template '{filename}' not found.",
                details={"path": str(file_path)}
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                cls._cache[filename] = content
                return content
        except Exception as e:
            raise StudyOSException(
                message=f"Failed to read prompt template '{filename}'.",
                details={"error": str(e)}
            ) from e

    @classmethod
    def format_prompt(cls, template_name: str, **kwargs: Any) -> str:
        """
        Load a template and inject the provided kwargs into its {placeholders}.
        
        Args:
            template_name: The name of the template file (without .txt).
            kwargs: Variables to inject into the template.
            
        Returns:
            The fully assembled prompt string ready for the LLM.
        """
        template_text = cls.get_template(template_name)
        
        try:
            # Use safe formatting. If a template expects a variable we didn't 
            # provide, Python's .format() will raise a KeyError.
            return template_text.format(**kwargs)
        except KeyError as e:
            logger.error(
                "Missing format variable %s for template '%s'", 
                str(e), template_name
            )
            raise StudyOSException(
                message="Failed to format prompt template.",
                details={"missing_variable": str(e), "template": template_name}
            ) from e
