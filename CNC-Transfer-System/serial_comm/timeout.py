"""
timeout.py

Responsabilidade única: controlar temporizadores de operação
(ex.: "essa transferência não pode durar mais que X segundos").
"""

import time


class OperationTimeout:
    def __init__(self, seconds: float):
        self.seconds = seconds
        self._start = None

    def start(self) -> None:
        self._start = time.monotonic()

    def expired(self) -> bool:
        if self._start is None:
            return False
        return (time.monotonic() - self._start) >= self.seconds

    def remaining(self) -> float:
        if self._start is None:
            return self.seconds
        left = self.seconds - (time.monotonic() - self._start)
        return max(0.0, left)

    def reset(self) -> None:
        self._start = time.monotonic()
