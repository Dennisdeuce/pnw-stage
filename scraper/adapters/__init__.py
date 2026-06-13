"""Adapter registry wiring.

Generic adapters (ICS/RSS/JSON/Ticketmaster/HTML) are configured entirely by a
venue/source `config` dict, so adding a venue is usually a config row — no code.
Bespoke adapters (e.g. STG) subclass when markup can't be expressed in config.
"""
from .base import Adapter, HttpClient, build_adapter
from .ics import ICSAdapter
from .rss import RSSAdapter
from .jsonfeed import JSONAdapter
from .ticketmaster import TicketmasterAdapter
from .html import HTMLAdapter
from .stg import STGAdapter
from .axs import AXSAdapter
from .dice import DICEAdapter

__all__ = [
    "Adapter",
    "HttpClient",
    "build_adapter",
    "ICSAdapter",
    "RSSAdapter",
    "JSONAdapter",
    "TicketmasterAdapter",
    "HTMLAdapter",
    "STGAdapter",
    "AXSAdapter",
    "DICEAdapter",
]
