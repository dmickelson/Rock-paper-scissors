"""Abstract importer protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from budget.models import Account, Transaction


class AbstractImporter(ABC):
    def __init__(self, account: Account) -> None:
        self.account = account

    @abstractmethod
    def parse(self, source) -> list[Transaction]:
        """Parse source (file path or email body string) into raw Transactions."""
        ...
