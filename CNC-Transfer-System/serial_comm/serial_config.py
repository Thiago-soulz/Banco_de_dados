"""
serial_config.py

Responsabilidade única: carregar, validar e salvar a configuração
da porta serial (porta, baudrate, paridade, stopbits, bytesize, timeout).

Não conhece nada sobre CNCs, drivers ou interface.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


DEFAULT_CONFIG_PATH = os.path.join("config", "serial.json")

VALID_PARITIES = {"N", "E", "O", "M", "S"}   # None, Even, Odd, Mark, Space
VALID_STOPBITS = {1, 1.5, 2}
VALID_BYTESIZES = {5, 6, 7, 8}


@dataclass
class SerialConfig:
    port: str = "COM1"
    baudrate: int = 9600
    parity: str = "E"
    stopbits: float = 1
    bytesize: int = 7
    timeout: float = 5.0          # segundos, leitura
    write_timeout: float = 5.0    # segundos, escrita
    xonxoff: bool = True          # controle de fluxo por software (comum em Fanuc/DNC)
    rtscts: bool = False          # controle de fluxo por hardware

    def validate(self) -> None:
        if not self.port:
            raise ValueError("Porta serial não informada.")
        if self.baudrate <= 0:
            raise ValueError(f"Baudrate inválido: {self.baudrate}")
        if self.parity not in VALID_PARITIES:
            raise ValueError(f"Paridade inválida: {self.parity}")
        if self.stopbits not in VALID_STOPBITS:
            raise ValueError(f"Stopbits inválido: {self.stopbits}")
        if self.bytesize not in VALID_BYTESIZES:
            raise ValueError(f"Bytesize inválido: {self.bytesize}")
        if self.timeout <= 0:
            raise ValueError("Timeout de leitura deve ser maior que zero.")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> SerialConfig:
    """Carrega a configuração a partir de um arquivo JSON.
    Se o arquivo não existir, retorna a configuração padrão."""
    if not os.path.exists(path):
        return SerialConfig()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    config = SerialConfig(**data)
    config.validate()
    return config


def save_config(config: SerialConfig, path: str = DEFAULT_CONFIG_PATH) -> None:
    """Salva a configuração atual em disco (formato JSON)."""
    config.validate()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=4, ensure_ascii=False)


def list_available_ports() -> list:
    """Lista as portas seriais disponíveis no sistema (requer pyserial)."""
    try:
        from serial.tools import list_ports
    except ImportError:
        raise ImportError(
            "pyserial não está instalado. Rode: pip install pyserial"
        )
    return [p.device for p in list_ports.comports()]
