"""Vercel entrypoint for the single-repository REX Observability application."""

from backend.core.rex_core import app

__all__ = ["app"]
