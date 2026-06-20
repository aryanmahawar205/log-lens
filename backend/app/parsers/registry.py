from typing import Dict, Type, List, Optional
from app.parsers.base import BaseParser

class ParserRegistry:
    """
    Registry system for log parsers.
    Allows automatic parser registration, discovery, and selection.
    """

    _parsers: Dict[str, Type[BaseParser]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a parser class.
        """
        def wrapper(parser_class: Type[BaseParser]):
            cls._parsers[name] = parser_class
            return parser_class
        return wrapper

    @classmethod
    def get_parser(cls, name: str) -> Optional[BaseParser]:
        """
        Get an instantiated parser by name.
        """
        parser_class = cls._parsers.get(name)
        if parser_class:
            return parser_class()
        return None

    @classmethod
    def list_parsers(cls) -> List[str]:
        """
        List all registered parser names.
        """
        return list(cls._parsers.keys())

    @classmethod
    def get_all_parsers(cls) -> Dict[str, BaseParser]:
        """
        Get instances of all registered parsers.
        """
        return {name: parser_class() for name, parser_class in cls._parsers.items()}
