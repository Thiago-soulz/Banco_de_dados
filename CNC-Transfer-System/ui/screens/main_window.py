import customtkinter as ctk
import threading
import queue
import os

from ui.screens.settings_window import SettingsWindow
from core.controller import Controller


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.controller = Controller()

        # Fila para receber dados do monitor de porta (thread de leitura -> UI)
        self._monitor_queue = queue.Queue()
        self._monitoring = False
        self._monitor_total_bytes = 0
        self._monitor_hex_mode = False

        self.title("CNC Transfer System")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_home_screen()

        self.show_screen("home")

    # ===================================================
    # SIDEBAR
    # ===================================================

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        title = ctk.CTkLabel(
            self.sidebar,
            text="CNC Transfer\nSystem",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(25, 10))

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="🔴 Desconectado",
            text_color="red",
            font=("Arial", 15)
        )
        self.status_label.pack(pady=15)

        # ----- Navegação -----
        self.nav_home_button = ctk.CTkButton(
            self.sidebar,
            text="🏠 Início / Transferência",
            command=lambda: self.show_screen("home")
        )
        self.nav_home_button.pack(fill="x", padx=20, pady=(0, 15))

        # ----- Ações -----
        self.connect_button = ctk.CTkButton(
            self.sidebar,
            text="Conectar",
            command=self.connect_machine
        )
        self.connect_button.pack(fill="x", padx=20, pady=5)

        self.receive_button = ctk.CTkButton(
            self.sidebar,
            text="Receber Programa",
            command=self.receive_program
        )
        self.receive_button.pack(fill="x", padx=20, pady=5)

        self.send_button = ctk.CTkButton(
            self.sidebar,
            text="Enviar Programa",
            command=self.send_program
        )
        self.send_button.pack(fill="x", padx=20, pady=5)

        self.config_button = ctk.CTkButton(
            self.sidebar,
            text="Configurações",
            command=self.settings
        )
        self.config_button.pack(fill="x", padx=20, pady=5)

        self.disconnect_button = ctk.CTkButton(
            self.sidebar,
            text="Desconectar",
            fg_color="#b71c1c",
            hover_color="#8e0000",
            command=self.disconnect_machine
        )
        self.disconnect_button.pack(fill="x", padx=20, pady=(40, 5))

    # ===================================================
    # NAVEGAÇÃO ENTRE TELAS
    # ===================================================

    def show_screen(self, name: str):
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

    # ===================================================
    # TELA PRINCIPAL (Recebimento + Monitor Integrado)
    # ===================================================

    def create_home_screen(self):
        frame = ctk.CTkFrame(self)
        self.home_frame = frame

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # ---------------- COLUNA ESQUERDA: RECEBER ----------------
        left_container = ctk.CTkFrame(frame, fg_color="transparent")
        left_container.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10)
        left_container.grid_columnconfigure(0, weight=1)
        left_container.grid_rowconfigure(1, weight=1)

        title_recv = ctk.CTkLabel(
            left_container,
            text="Monitor de Recebimento",
            font=("Arial", 20, "bold")
        )
        title_recv.grid(row=0, column=0, pady=(5, 10), sticky="w")

        self.terminal = ctk.CTkTextbox(
            left_container,
            font=("Consolas", 13)
        )
        self.terminal.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        self.progress = ctk.CTkProgressBar(left_container)
        self.progress.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress.set(0)

        self.bytes_label = ctk.CTkLabel(
            left_container,
            text="Recebidos: 0 bytes"
        )
        self.bytes_label.grid(row=3, column=0, pady=5)

        # ---------------- COLUNA DIREITA: MONITOR DE LINHA ----------------
        right_container = ctk.CTkFrame(frame, fg_color="transparent")
        right_container.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=10, pady=10)
        right_container.grid_columnconfigure(0, weight=1)
        right_container.grid_rowconfigure(2, weight=1)

        title_mon = ctk.CTkLabel(
            right_container,
            text="Monitor de Linha (Tempo Real)",
            font=("Arial", 20, "bold")
        )
        title_mon.grid(row=0, column=0, pady=(5, 5), sticky="w")

        # Controles do Monitor Interno
        controls = ctk.CTkFrame(right_container, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.monitor_button = ctk.CTkButton(
            controls,
            text="▶ Iniciar Monitor",
            fg_color="#1565c0",
            hover_color="#0d47a1",
            command=self.toggle_monitor,
            width=120
        )
        self.monitor_button.pack(side="left", padx=(0, 10))

        self.hex_switch = ctk.CTkSwitch(
            controls,
            text="HEX",
            command=self.toggle_hex_mode
        )
        self.hex_switch.pack(side="left", padx=(0, 10))

        self.monitor_bytes_label = ctk.CTkLabel(
            controls,
            text="0 bytes"
        )
        self.monitor_bytes_label.pack(side="left", padx=5)

        # Terminal do Monitor
        self.monitor_terminal = ctk.CTkTextbox(
            right_container,
            font=("Consolas", 13)
        )
        self.monitor_terminal.grid(row=2, column=0, sticky="nsew")

    def log(self, text):
        self.terminal.insert("end", text + "\n")
        self.terminal.see("end")

    def monitor_log(self, text):
        self.monitor_terminal.insert("end", text + "\n")
        self.monitor_terminal.see("end")

    def clear_terminals(self):
        """Limpa as caixas de texto dos dois terminais antes de uma nova operação."""
        self.terminal.delete("1.0", "end")
        self.monitor_terminal.delete("1.0", "end")

    # ===================================================
    # LÓGICA DO MONITOR DE LINHA
    # ===================================================

    def toggle_hex_mode(self):
        self._monitor_hex_mode = bool(self.hex_switch.get())

    def toggle_monitor(self):
        if self._monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()

    def start_monitor(self, silent=False):
        if self._monitoring:
            return True

        if not self.controller.manager.is_open:
            self.monitor_log("Conecte-se à máquina antes de monitorar.")
            return False

        self._monitor_total_bytes = 0
        self.monitor_bytes_label.configure(text="0 bytes")

        try:
            self.controller.start_monitor(
                on_data=lambda chunk: self._monitor_queue.put(chunk)
            )
        except Exception as e:
            self.monitor_log(f"Erro ao iniciar monitor: {e}")
            return False

        self._monitoring = True
        self.monitor_button.configure(
            text="■ Parar",
            fg_color="#b71c1c",
            hover_color="#8e0000",
            state="disabled",
        )
        self.after(300, lambda: self.monitor_button.configure(state="normal"))

        if not silent:
            self.monitor_log("=== Monitor iniciado ===")
        
        self._poll_monitor_queue()
        return True

    def stop_monitor(self):
        if not self._monitoring:
            return

        self.controller.stop_monitor()
        self._monitoring = False

        self.monitor_button.configure(
            text="▶ Iniciar Monitor",
            fg_color="#1565c0",
            hover_color="#0d47a1",
            state="disabled",
        )
        self.after(300, lambda: self.monitor_button.configure(state="normal"))

        self.monitor_log(f"=== Monitor parado ({self._monitor_total_bytes} bytes) ===")

    def _poll_monitor_queue(self):
        try:
            while True:
                chunk = self._monitor_queue.get_nowait()
                self._monitor_total_bytes += len(chunk)

                if self._monitor_hex_mode:
                    text = " ".join(f"{b:02X}" for b in chunk)
                else:
                    text = chunk.decode("ascii", errors="replace")

                self.monitor_log(text)
                self.monitor_bytes_label.configure(
                    text=f"{self._monitor_total_bytes} bytes"
                )
        except queue.Empty:
            pass

        if self._monitoring:
            self.after(100, self._poll_monitor_queue)

    # ===================================================
    # OPERAÇÕES DE CONEXÃO E RECEBIMENTO
    # ===================================================

    # ===================================================
    # OPERAÇÕES DE CONEXÃO E RECEBIMENTO
    # ===================================================

    def connect_machine(self):
        self.log("Conectando...")
        
        # Desativa temporariamente o botão para evitar cliques duplos durante a tentativa
        self.connect_button.configure(state="disabled")
        self.update_idletasks()
        
        ok = self.controller.connect_machine()

        if ok:
            self.status_label.configure(text="🟢 Conectado", text_color="green")
            self.log("Conectado com sucesso.")
            
            # TRANCA o botão de Conectar e as Configurações com a porta aberta
            self.connect_button.configure(state="disabled")
            self.config_button.configure(state="disabled")
            self.disconnect_button.configure(state="normal")
        else:
            self.status_label.configure(text="🔴 Falha", text_color="red")
            self.log("Erro ao conectar.")
            
            # Se falhar, LIBERA o botão de Conectar para tentar de novo
            self.connect_button.configure(state="normal")
            self.config_button.configure(state="normal")

    def disconnect_machine(self):
        if self._monitoring:
            self.stop_monitor()

        self.controller.disconnect_machine()
        self.status_label.configure(text="🔴 Desconectado", text_color="red")
        self.log("Desconectado.")
        
        # LIBERA os botões novamente para novas ações ou mudanças de porta
        self.connect_button.configure(state="normal")
        self.config_button.configure(state="normal")

    def receive_program(self):
        # 1. Verifica se a porta está aberta antes de iniciar
        if not self.controller.manager.is_open:
            self.clear_terminals()
            self.log("Erro: Conecte-se à máquina antes de receber programas.")
            return

        # Bloqueia ações paralelas enquanto uma transferência está rodando
        self.disconnect_button.configure(state="disabled")
        self.receive_button.configure(state="disabled")
        self.send_button.configure(state="disabled")

        # 2. Reseta o visual e exibe os avisos de espera
        self.clear_terminals()
        self.progress.set(0)
        
        self.log("Aguardando comunicação com a máquina...")
        self.monitor_log("=== Monitor iniciado automaticamente ===")
        self.monitor_log("Aguardando comunicação com a máquina...")

        # 3. Garante que o monitoramento de linha está rodando em paralelo
        self.start_monitor(silent=True)

        # 4. Inicia a thread que aguarda os dados efetivos do arquivo
        thread = threading.Thread(
            target=self.receive_thread,
            daemon=True
        )
        thread.start()

    def receive_thread(self):
        try:
            save_dir = os.path.join("storage", "received")
            paths = self.controller.receive_program(save_dir)
            
            self.progress.set(1)

            self.log("----------------------------------")
            self.log("Programa(s) recebido(s) com sucesso.")
            for path in paths:
                size = os.path.getsize(path)
                self.log(f"Arquivo: {path} ({size} bytes)")
            self.log("----------------------------------")
        
        except Exception as e:
            self.log("")
            self.log("ERRO / TIMEOUT")
            self.log(str(e))
            self.monitor_log(f"Status: Transferência encerrada ou abortada. ({e})")
        
        finally:
            # Libera o painel de controle assim que a operação termina (por sucesso ou erro)
            self.disconnect_button.configure(state="normal")
            self.receive_button.configure(state="normal")
            self.send_button.configure(state="normal")
    def send_program(self):
        """Função de envio de programas para o CNC."""
        self.log("Função de envio ainda será implementada.")
    def settings(self):
        """Abre a janela secundária de configurações serial."""
        # Abre a janela passando a MainWindow (self) como parente
        SettingsWindow(self)