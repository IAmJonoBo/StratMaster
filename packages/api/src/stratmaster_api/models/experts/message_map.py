"""Message map model for structured communication templates."""

from .base import WithMeta


class MessageMap(WithMeta):
    """Structured message template following audience→problem→value→proof→CTA pattern."""
    
    audience: str
    problem: str
    value: str
    proof: str
    cta: str