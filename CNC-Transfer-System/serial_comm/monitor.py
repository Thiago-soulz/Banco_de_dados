"""
monitor.py

Responsabilidade única: ficar "escutando" a porta serial em segundo
plano e repassar cada pedaço de dado recebido para quem estiver
interessado (normalmente a UI), via callback.

Diferente de receiver.py, este módulo não sabe nada sobre onde o
programa começa ou termina — ele só relata o que passa pelo cabo,
byte a byte, em tempo real. Serve para depuração e para a tela de
"Monitor de Linha".

Não sabe nada sobre arquivos, banco de dados ou interface.
"""

import logging
import threading
import time

from .serial_manager import SerialManager

logger = logging.getLogger("serial_comm.monitor")


class PortMonitor:
    """Lê a porta serial continuamente em uma thread separada e chama
    `on_data(chunk: bytes)` para cada pedaço de dado que chegar.

    Uso típico:

        monitor = PortMonitor(manager, on_data=minha_funcao)
        monitor.start()
        ...
        monitor.stop()

    `on_data` é chamado a partir da thread de leitura, NÃO da thread
    principal — se for atualizar uma UI (Tkinter/customtkinter), não
    mexa em widgets diretamente dentro do callback; em vez disso,
    empilhe os dados em uma fila (queue.Queue) e processe-os no loop
    principal da UI (ex.: via `after()`).
    """

    def __init__(self, manager: SerialManager, on_data, chunk_size: int = 64,
                 poll_interval: float = 0.05):
        self.manager = manager
        self.on_data = on_data
        self.chunk_size = chunk_size
        self.poll_interval = poll_interval

        self._thread = None
        self._stop_event = threading.Event()
        self._bytes_seen = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def bytes_seen(self) -> int:
        return self._bytes_seen

    def start(self) -> None:
        if self.is_running:
            return

        self._stop_event.clear()
        self._bytes_seen = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Monitor de porta iniciado.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("Monitor de porta parado (%d bytes observados).", self._bytes_seen)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                conn = self.manager.raw()
                chunk = conn.read(self.chunk_size)
            except Exception as e:
                logger.warning("Erro de leitura no monitor: %s", e)
                time.sleep(0.5)
                continue

            if chunk:
                self._bytes_seen += len(chunk)
                try:
                    self.on_data(chunk)
                except Exception:
                    logger.exception("Erro no callback do monitor.")
            else:
                # nada chegou neste ciclo; evita busy-loop
                time.sleep(self.poll_interval)
