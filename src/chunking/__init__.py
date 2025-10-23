"""
Text chunking module.

RECOMMENDED: Use create_chunker() with default settings.
"""

from chunking.base_chunker import BaseChunker
from chunking.langchain_chunker import LangChainChunker
from chunking.factory import create_chunker, get_chunker_info

__all__ = [
    'BaseChunker',
    'LangChainChunker',
    'create_chunker',
    'get_chunker_info'
]
