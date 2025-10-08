"""
Execution type enumerations for MCI.

This module defines the execution types supported by the MCI adapter,
including HTTP requests, CLI commands, file reading, and text templates.
"""

from enum import Enum


class ExecutionType(str, Enum):
    """
    Defines the types of execution supported by MCI.

    Each execution type corresponds to a different way of executing a tool:
    - HTTP: Make HTTP requests to APIs
    - CLI: Execute command-line tools
    - FILE: Read and parse files
    - TEXT: Return text with placeholder substitution
    """

    HTTP = "http"
    CLI = "cli"
    FILE = "file"
    TEXT = "text"
