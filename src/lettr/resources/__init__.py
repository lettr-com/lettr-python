"""Lettr API resource modules."""

from .audience import Audience
from .campaigns import Campaigns
from .domains import Domains
from .emails import Emails
from .projects import Projects
from .templates import Templates
from .webhooks import Webhooks

__all__ = ["Audience", "Campaigns", "Domains", "Emails", "Projects", "Templates", "Webhooks"]
