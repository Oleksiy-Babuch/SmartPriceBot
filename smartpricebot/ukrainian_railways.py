"""Extension point for permitted Ukrainian Railways ticket notifications.

Implement a provider using an official API or another permitted source. Keeping this
interface isolated means it can share Telegram notifications without touching the
price scraping code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class TicketWatch:
    departure: str
    arrival: str
    travel_date: date
    passengers: int = 1


@dataclass(frozen=True)
class TicketAvailability:
    watch: TicketWatch
    available: bool
    details: str = ""


class UkrainianRailwaysProvider(Protocol):
    """Contract for a future, officially permitted ticket data provider."""

    async def availability(self, watch: TicketWatch) -> TicketAvailability: ...
