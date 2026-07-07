"""
serial_manager.py

Responsabilidade única: abrir, fechar e manter viva a conexão
com a porta serial. Não sabe nada sobre protocolo de CNC.

Fase 0.1 Alpha do roadmap: "Abrir a porta serial".
"""

import logging
from .serial_config import SerialConfig

logger = logging.getLogger("serial_comm.serial_manager")


class SerialConnectionError(Exception):
    pass


class SerialManager:
    def __init__(self, config: SerialConfig):
        self.config = config
        self._conn = None

    @property
    def is_open(self) -> bool:
        return self._conn is not None and self._conn.is_open

    def connect(self):
        """Abre a porta serial usando pyserial. Lança SerialConnectionError
        se não conseguir abrir."""
        try:
            import serial as pyserial  # pyserial, não confundir com este pacote
        except ImportError as e:
            raise SerialConnectionError(
                "pyserial não instalado. Rode: pip install pyserial"
            ) from e

        parity_map = {
            "N": pyserial.PARITY_NONE,
            "E": pyserial.PARITY_EVEN,
            "O": pyserial.PARITY_ODD,
            "M": pyserial.PARITY_MARK,
            "S": pyserial.PARITY_SPACE,
        }
        stopbits_map = {
            1: pyserial.STOPBITS_ONE,
            1.5: pyserial.STOPBITS_ONE_POINT_FIVE,
            2: pyserial.STOPBITS_TWO,
        }
        bytesize_map = {
            5: pyserial.FIVEBITS,
            6: pyserial.SIXBITS,
            7: pyserial.SEVENBITS,
            8: pyserial.EIGHTBITS,
        }

        try:
            self._conn = pyserial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                parity=parity_map[self.config.parity],
                stopbits=stopbits_map[self.config.stopbits],
                bytesize=bytesize_map[self.config.bytesize],
                timeout=self.config.timeout,
                write_timeout=self.config.write_timeout,
                xonxoff=self.config.xonxoff,
                rtscts=self.config.rtscts,
            )
            logger.info("Porta %s aberta (%s bps).", self.config.port, self.config.baudrate)
        except Exception as e:
            raise SerialConnectionError(
                f"Falha ao abrir a porta {self.config.port}: {e}"
            ) from e

        return self._conn

    def disconnect(self) -> None:
        if self._conn and self._conn.is_open:
            self._conn.close()
            logger.info("Porta %s fechada.", self.config.port)
        self._conn = None

    def raw(self):
        """Retorna o objeto pyserial.Serial cru, para uso por receiver/sender."""
        if not self.is_open:
            raise SerialConnectionError("A porta não está aberta.")
        return self._conn

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
