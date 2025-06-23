"""LLM-MD: A CLI tool for generating LLM context from GitHub repositories."""

try:
    from importlib.metadata import version
    __version__ = version('llmd')
except ImportError:
    __version__ = "dev"