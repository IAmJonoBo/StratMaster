"""Refactor boundary enforcement."""
from .boundary_checker import BoundaryIssue, check_boundaries  # noqa: F401

__all__ = ["BoundaryIssue", "check_boundaries"]
