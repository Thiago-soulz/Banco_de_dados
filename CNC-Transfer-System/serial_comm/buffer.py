"""
buffer.py

Responsabilidade única: acumular bytes recebidos pela porta serial
e oferecer utilitários simples de busca/corte, sem saber nada sobre
protocolo de CNC específico.
"""


class SerialBuffer:
    def __init__(self):
        self._data = bytearray()

    def append(self, chunk: bytes) -> None:
        self._data.extend(chunk)

    def contains(self, marker: bytes) -> bool:
        return marker in self._data

    def find(self, marker: bytes) -> int:
        return self._data.find(marker)

    def raw(self) -> bytes:
        return bytes(self._data)

    def length(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        self._data = bytearray()

    def pop_all(self) -> bytes:
        """Retorna todos os bytes acumulados e limpa o buffer."""
        data = bytes(self._data)
        self.clear()
        return data
