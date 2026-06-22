from typing import Dict, Type, List, Optional
from app.parsers.base import BaseParser
import importlib
import pkgutil
import inspect

class ParserRegistry:
    """
    Registry system for log parsers.
    Allows automatic parser registration, discovery, and selection.
    """

    _parsers: Dict[str, Type[BaseParser]] = {}

    _initialized = False

    @classmethod
    def _discover_plugins(cls):
        """
        Auto-discover and load parsers.
        """
        if cls._initialized:
            return

        # Load all modules inside app.parsers package
        import app.parsers
        for _, module_name, _ in pkgutil.iter_modules(app.parsers.__path__):
            # Exclude base and registry to avoid circular logic
            if module_name in ('base', 'registry', 'detector', 'ai_parser'):
                continue
            try:
                importlib.import_module(f'app.parsers.{module_name}')
            except Exception:
                pass

        cls._initialized = True

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
        cls._discover_plugins()
        """
        Get an instantiated parser by name.
        """
        parser_class = cls._parsers.get(name)
        if parser_class:
            return parser_class()
        return None

    @classmethod
    def list_parsers(cls) -> List[str]:
        cls._discover_plugins()
        """
        List all registered parser names.
        """
        return list(cls._parsers.keys())

    @classmethod
    def get_all_parsers(cls) -> Dict[str, BaseParser]:
        cls._discover_plugins()
        """
        Get instances of all registered parsers.
        """
        return {name: parser_class() for name, parser_class in cls._parsers.items()}
