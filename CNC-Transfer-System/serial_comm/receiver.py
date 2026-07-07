"""
receiver.py

Responsabilidade única: RECEBER bytes vindos do CNC pela porta serial
e devolver o conteúdo (texto do programa) ao chamador.

Não sabe nada sobre arquivos, banco de dados ou interface.
"""

import logging
from .serial_manager import SerialManager
from .buffer import SerialBuffer
from .timeout import OperationTimeout
from . import handshake as hs

logger = logging.getLogger("serial_comm.receiver")


class ReceiveTimeoutError(Exception):
    pass


def receive_program(
    manager: SerialManager,
    end_marker: bytes = hs.EOT,
    max_seconds: float = 120.0,
    chunk_size: int = 256,
) -> bytes:
    """
    Lê bytes da porta serial até encontrar `end_marker` (por padrão EOT,
    comum em transferências ISO/Fanuc) ou até estourar `max_seconds`.

    Retorna os bytes recebidos (sem o marcador final).
    """
    conn = manager.raw()
    buf = SerialBuffer()
    timer = OperationTimeout(max_seconds)
    timer.start()

    logger.info("Aguardando recepção de programa (timeout %.0fs)...", max_seconds)

    while not timer.expired():
        chunk = conn.read(chunk_size)
        if chunk:
            buf.append(chunk)
            if buf.contains(end_marker):
                break
        # se chunk vier vazio, apenas o timeout do pyserial já passou
        # um pequeno intervalo; o loop continua até `max_seconds` total.

    if not buf.contains(end_marker):
        raise ReceiveTimeoutError(
            f"Timeout: nenhum programa recebido em {max_seconds:.0f}s "
            f"({buf.length()} bytes acumulados)."
        )

    raw = buf.raw()
    idx = raw.find(end_marker)
    program = raw[:idx]

    logger.info("Programa recebido: %d bytes.", len(program))
    return program


def receive_program_until_idle(
    manager: SerialManager,
    idle_seconds: float = 3.0,
    max_seconds: float = 120.0,
    chunk_size: int = 256,
    max_reconnect_attempts: int = 5,
) -> bytes:
    """
    Modo alternativo de recepção: em vez de esperar um caractere de
    fim de transmissão (EOT), considera o programa completo quando a
    porta fica `idle_seconds` sem receber nenhum byte novo.

    Muitos softwares DNC (como o NCLink) não enviam um marcador de fim
    explícito — eles simplesmente param de transmitir quando o
    programa acaba. Esse modo cobre esse caso.

    Alguns adaptadores USB-serial soltam a porta por uma fração de
    segundo quando a máquina começa a transmitir (erro típico:
    "ClearCommError failed" / PermissionError). Quando isso acontece,
    esta função tenta reconectar automaticamente (até
    `max_reconnect_attempts` vezes) em vez de desistir, para não
    perder o início da transferência.

    Esta função NUNCA descarta dados: mesmo em caso de timeout total,
    erro de leitura na porta, ou desconexão no meio da transferência,
    ela retorna tudo o que já foi recebido até aquele momento (mesmo
    que incompleto). Só retorna vazio (b"") se nenhum byte tiver
    chegado.
    """
    import time

    buf = SerialBuffer()
    total_timer = OperationTimeout(max_seconds)
    total_timer.start()

    idle_timer = OperationTimeout(idle_seconds)

    logger.info(
        "Aguardando recepção por inatividade (idle %.1fs, timeout total %.0fs)...",
        idle_seconds, max_seconds,
    )

    received_anything = False
    reconnect_attempts = 0

    while not total_timer.expired():
        try:
            conn = manager.raw()
            chunk = conn.read(chunk_size)
        except Exception as e:
            reconnect_attempts += 1
            logger.warning(
                "Erro de leitura na porta (tentativa %d/%d): %s (bytes acumulados: %d). "
                "Tentando reconectar...",
                reconnect_attempts, max_reconnect_attempts, e, buf.length(),
            )
            if reconnect_attempts > max_reconnect_attempts:
                logger.error("Excedido o número de tentativas de reconexão. Encerrando recepção.")
                break
            try:
                manager.disconnect()
            except Exception:
                pass
            time.sleep(0.5)
            try:
                manager.connect()
            except Exception as reconnect_error:
                logger.warning("Falha ao reconectar: %s", reconnect_error)
            continue

        if chunk:
            buf.append(chunk)
            received_anything = True
            idle_timer.reset()
            reconnect_attempts = 0  # zera contador após sucesso
        else:
            if received_anything and idle_timer.expired():
                break

    if not received_anything:
        logger.warning("Nenhum byte foi recebido em %.0fs.", max_seconds)

    program = buf.raw()
    logger.info("Programa recebido (modo idle): %d bytes.", len(program))
    return program
