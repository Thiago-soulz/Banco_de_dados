"""
sender.py

Responsabilidade única: ENVIAR bytes (um programa CNC) pela porta
serial para a máquina.
"""

import logging
from .serial_manager import SerialManager
from . import handshake as hs

logger = logging.getLogger("serial_comm.sender")


class SendError(Exception):
    pass


def send_program(
    manager: SerialManager,
    data: bytes,
    end_marker: bytes = hs.EOT,
    chunk_size: int = 256,
) -> int:
    """
    Envia `data` pela porta serial em blocos de `chunk_size` bytes,
    finalizando com `end_marker`.

    Retorna o número total de bytes enviados (incluindo o marcador final).
    """
    conn = manager.raw()
    payload = data + end_marker
    sent_total = 0

    try:
        for i in range(0, len(payload), chunk_size):
            block = payload[i:i + chunk_size]
            conn.write(block)
            conn.flush()
            sent_total += len(block)
    except Exception as e:
        raise SendError(f"Falha ao enviar dados: {e}") from e

    logger.info("Programa enviado: %d bytes.", sent_total)
    return sent_total
