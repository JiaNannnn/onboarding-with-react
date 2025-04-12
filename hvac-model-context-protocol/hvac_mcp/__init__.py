"""
HVAC Model Context Protocol package.

This package provides a structured framework for LLMs to consistently reason
about HVAC systems and point mappings, enhancing accuracy and explainability.
"""

__version__ = "1.0.0"

from .engine import ProtocolEngine
from .ontology import load_ontology
from .kb import load_knowledge_base
from .templates import get_reasoning_template, format_protocol_context

__all__ = [
    'ProtocolEngine', 
    'load_ontology', 
    'load_knowledge_base',
    'get_reasoning_template',
    'format_protocol_context'
] 