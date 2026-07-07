"""
program_splitter.py

Quando o NCLink faz backup de uma pasta inteira, todos os programas
chegam concatenados em um único bloco de bytes. Este módulo detecta
os cabeçalhos de cada programa dentro desse bloco e separa tudo em
arquivos individuais, usando o nome real do programa.

Padrões reconhecidos:
  Siemens: %_N_<NOME>_MPF, %_N_<NOME>_SPF, ou qualquer outro sufixo
           (ex: %_N_DPWP_INI, %_N_TOA_EQUINOX_TOA) — o sufixo não é
           fixo, então aceitamos qualquer coisa depois de %_N_.
  Fanuc:   O1000, O0001, etc. (letra O maiúscula + dígitos, início de
           linha).

Se nenhum cabeçalho for reconhecido, o blob inteiro é tratado como um
único programa (fallback).
"""

import re
from dataclasses import dataclass

# Siemens: %_N_ seguido de qualquer coisa até o fim da linha (CR/LF)
_SIEMENS_HEADER = re.compile(rb"^%_N_([^\r\n]+)", re.MULTILINE)

# Fanuc: O seguido de 1 a 4 dígitos, início de linha
_FANUC_HEADER = re.compile(rb"^O(\d{1,4})\b", re.MULTILINE)


@dataclass
class SplitProgram:
    name: str
    content: bytes


def split_programs(data: bytes) -> list[SplitProgram]:
    """Divide um blob de bytes em programas individuais.

    Retorna uma lista de SplitProgram. Se nenhum cabeçalho reconhecido
    for encontrado, retorna uma lista com um único item cujo nome é
    None (o chamador deve decidir o nome de fallback).
    """
    matches = list(_SIEMENS_HEADER.finditer(data))
    is_fanuc = False

    if not matches:
        matches = list(_FANUC_HEADER.finditer(data))
        is_fanuc = True

    if not matches:
        return [SplitProgram(name=None, content=data)]

    programs = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(data)
        chunk = data[start:end]

        if is_fanuc:
            name = f"O{match.group(1).decode('ascii', errors='replace')}"
        else:
            name = match.group(1).decode("ascii", errors="replace").strip()

        # Sanitiza o nome para uso seguro como nome de arquivo
        name = re.sub(r"[^A-Za-z0-9_\-\.]", "_", name)

        programs.append(SplitProgram(name=name, content=chunk))

    return programs
