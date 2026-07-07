"""
controller.py

O Core do sistema. Nenhuma tela (terminal ou GUI) fala diretamente
com a porta serial — tudo passa por aqui.
"""

import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serial_comm.serial_manager import SerialManager, SerialConnectionError
from serial_comm.serial_config import SerialConfig, load_config
from serial_comm.receiver import receive_program, receive_program_until_idle, ReceiveTimeoutError
from serial_comm.sender import send_program, SendError
from serial_comm.monitor import PortMonitor
from utils.program_splitter import split_programs

logger = logging.getLogger("core.controller")


class Controller:
    def reload_config(self):
        """Força a recarga das configurações do JSON diretamente para a conexão ativa."""
        try:
            # 1. Se a porta atual estiver aberta, fecha para liberar o hardware
            if hasattr(self, 'manager') and self.manager.is_open:
                self.disconnect_machine()
            
            # 2. Força o recarregamento das configurações lendo o JSON limpo
            from serial_comm.serial_config import load_config
            self.config = load_config()
            
            # 3. Atualiza as configurações dentro do seu gerenciador serial
            if hasattr(self, 'manager'):
                self.manager.config = self.config
                # Tenta atualizar o serial_manager de acordo com a estrutura do seu projeto
                if hasattr(self.manager, 'load_config'):
                    self.manager.load_config()
                elif hasattr(self.manager, 'init_serial'):
                    self.manager.init_serial()
                
                # Sincroniza a porta diretamente no objeto serial interno do PySerial se ele existir
                if hasattr(self.manager, 'serial') and self.manager.serial:
                    self.manager.serial.port = self.config.port
                    self.manager.serial.baudrate = self.config.baudrate
                    self.manager.serial.bytesize = self.config.bytesize
                    self.manager.serial.parity = self.config.parity
                    self.manager.serial.stopbits = self.config.stopbits
                    self.manager.serial.timeout = self.config.timeout
                    self.manager.serial.xonxoff = self.config.xonxoff
                    self.manager.serial.rtscts = self.config.rtscts

            print(f"[SUCCESS] Configurações aplicadas com sucesso para a porta: {self.config.port}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao recarregar configurações no Controller: {e}")
            return False
    
    def __init__(self, config: SerialConfig = None):
        self.config = config or load_config()
        self.manager = SerialManager(self.config)
        self._monitor: PortMonitor = None

    def connect_machine(self) -> bool:
        try:
            self.manager.connect()
            return True
        except SerialConnectionError as e:
            logger.error(str(e))
            return False

    def disconnect_machine(self) -> None:
        self.manager.disconnect()

    def get_status(self) -> str:
        return "Conectado" if self.manager.is_open else "Desconectado"

    def receive_program(self, dest_dir: str, base_name: str = None,
                         max_seconds: float = 120.0, idle_seconds: float = 3.0):
        """Recebe dados da máquina e salva em `dest_dir`.

        Usa detecção por inatividade (a transmissão termina quando a
        porta fica `idle_seconds` sem receber bytes novos), que é o
        comportamento mais comum em softwares DNC como o NCLink.

        Se o bloco recebido contiver múltiplos programas concatenados
        (backup de pasta inteira, com cabeçalhos %_N_... da Siemens ou
        Onnnn da Fanuc), cada programa é separado e salvo em um
        arquivo .txt individual, nomeado com o nome real do programa.
        Se nenhum cabeçalho for reconhecido, salva tudo em um único
        arquivo .txt usando `base_name` (ou um nome automático).

        Sempre salva em disco o que foi recebido, mesmo que a
        transferência tenha sido interrompida no meio.

        Retorna a lista de caminhos salvos (list[str])."""
        if not self.manager.is_open:
            raise SerialConnectionError("Conecte-se à máquina antes de receber.")

        data = receive_program_until_idle(self.manager, idle_seconds=idle_seconds, max_seconds=max_seconds)
        os.makedirs(dest_dir, exist_ok=True)

        if len(data) == 0:
            logger.warning("Nenhum byte foi recebido.")

        programs = split_programs(data)
        saved_paths = []

        if len(programs) == 1 and programs[0].name is None:
            # Nenhum cabeçalho reconhecido: salva como um único arquivo
            name = base_name or "recebido"
            path = os.path.join(dest_dir, f"{name}.txt")
            path = self._unique_path(path)
            with open(path, "wb") as f:
                f.write(programs[0].content)
            saved_paths.append(path)
        else:
            for prog in programs:
                path = os.path.join(dest_dir, f"{prog.name}.txt")
                path = self._unique_path(path)
                with open(path, "wb") as f:
                    f.write(prog.content)
                saved_paths.append(path)

        return saved_paths

    @staticmethod
    def _unique_path(path: str) -> str:
        """Evita sobrescrever arquivo existente, adicionando um sufixo numérico."""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(f"{base}_{i}{ext}"):
            i += 1
        return f"{base}_{i}{ext}"

    def send_program(self, file_path: str) -> int:
        """Lê um arquivo do disco e envia para a máquina."""
        if not self.manager.is_open:
            raise SerialConnectionError("Conecte-se à máquina antes de enviar.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        return send_program(self.manager, data)

    # ===================================================
    # MONITOR DE LINHA (leitura passiva do cabo)
    # ===================================================

    def start_monitor(self, on_data) -> None:
        """Começa a observar tudo que chega pela porta serial, em segundo
        plano, chamando `on_data(chunk: bytes)` para cada trecho recebido.

        Não interfere no envio/recebimento normal de programas — serve
        para uma tela de monitoramento em tempo real do que passa pelo
        cabo de dados.
        """
        if not self.manager.is_open:
            raise SerialConnectionError("Conecte-se à máquina antes de monitorar.")

        if self._monitor is not None and self._monitor.is_running:
            return

        self._monitor = PortMonitor(self.manager, on_data=on_data)
        self._monitor.start()

    def stop_monitor(self) -> None:
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor = None

    @property
    def is_monitoring(self) -> bool:
        return self._monitor is not None and self._monitor.is_running
