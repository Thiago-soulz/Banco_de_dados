"""
handshake.py

Responsabilidade única: encapsular os sinais de controle de fluxo
usados por controladores CNC via RS-232 (DC1/DC3, XON/XOFF, ENQ/ACK).

Cada "driver" de máquina (drivers/fanuc, drivers/siemens, ...) decide
quais desses sinais usar; este módulo só define as constantes e
funções auxiliares comuns.
"""

# Caracteres de controle mais usados em transferência DNC/CNC
DC1 = b"\x11"   # XON  - "pode enviar" (usado por muitos Fanuc para liberar envio)
DC3 = b"\x13"   # XOFF - "pare de enviar" (buffer da máquina cheio)
ENQ = b"\x05"   # Enquiry
ACK = b"\x06"   # Acknowledge
NAK = b"\x15"   # Negative acknowledge
EOT = b"\x04"   # End of transmission
ETX = b"\x03"   # End of text
STX = b"\x02"   # Start of text


def is_xon(byte: bytes) -> bool:
    return byte == DC1

def is_xoff(byte: bytes) -> bool:
    return byte == DC3

def is_ack(byte: bytes) -> bool:
    return byte == ACK

def is_nak(byte: bytes) -> bool:
    return byte == NAK
