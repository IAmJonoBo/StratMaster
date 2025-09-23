"""Adapters for external integrations."""

from .checkers import run_checks_for_discipline
from .doctrine_loader import load_doctrines

__all__ = ["run_checks_for_discipline", "load_doctrines"]