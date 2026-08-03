"""Small JSON store so GitHub Actions can preserve price history in Git."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import PriceObservation


class HistoryStore:
    def __init__(self, path: Path, max_entries_per_product: int = 100) -> None:
        self.path = path
        self.max_entries_per_product = max_entries_per_product

    def read(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"History file is not valid JSON: {self.path}") from error
        if not isinstance(data, dict):
            raise ValueError("History file must contain an object.")
        return data

    def latest(self, product_id: str) -> dict[str, Any] | None:
        values = self.read().get(product_id, [])
        return values[-1] if values else None

    def append(self, observation: PriceObservation) -> None:
        data = self.read()
        values = data.setdefault(observation.product_id, [])
        values.append(observation.to_dict())
        data[observation.product_id] = values[-self.max_entries_per_product :]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
