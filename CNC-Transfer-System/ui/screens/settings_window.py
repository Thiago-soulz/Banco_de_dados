import json
import os
import customtkinter as ctk


class SettingsWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.title("Recieve settings")
        self.geometry("480x420")
        self.resizable(False, False)

        # Caminho do arquivo JSON
        self.config_path = os.path.join("config", "serial.json")

        # Configurações padrão de fallback caso o arquivo falhe
        self.config_data = {
            "port": "COM4",
            "baudrate": 9600,
            "parity": "E",
            "stopbits": 2,
            "bytesize": 7,
            "timeout": 5.0,
            "xonxoff": True,
            "rtscts": False  # Corrigido aqui de rtsxcts para rtscts
        }

        self.load_config()

        # Fazer com que a janela apareça na frente e capture o foco (Modal)
        self.transient(parent)
        self.grab_set()

        # Layout Grid
        self.grid_columnconfigure((0, 1), weight=1, pad=10)

        # --- Elementos Visuais ---

        # Porta (Comm Port)
        ctk.CTkLabel(self, text="Comm Port:").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.port_menu = ctk.CTkOptionMenu(
            self,
            values=[f"COM{i}" for i in range(1, 16)],
            width=140
        )
        self.port_menu.grid(row=0, column=0, padx=20, pady=(0, 10), sticky="e")

        # Baud rate
        ctk.CTkLabel(self, text="Baud rate:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.baud_menu = ctk.CTkOptionMenu(
            self,
            values=["1200", "2400", "4800", "9600", "19200", "38400", "115200"],
            width=140
        )
        self.baud_menu.grid(row=1, column=0, padx=20, pady=5, sticky="e")

        # Data bits
        ctk.CTkLabel(self, text="Data bits:").grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        self.bits_menu = ctk.CTkOptionMenu(
            self,
            values=["5", "6", "7", "8"],
            width=140
        )
        self.bits_menu.grid(row=0, column=1, padx=20, pady=(0, 10), sticky="e")

        # Parity
        ctk.CTkLabel(self, text="Parity:").grid(row=1, column=1, padx=20, pady=5, sticky="w")
        self.parity_menu = ctk.CTkOptionMenu(
            self,
            values=["NONE", "EVEN", "ODD", "MARK", "SPACE"],
            width=140
        )
        self.parity_menu.grid(row=1, column=1, padx=20, pady=5, sticky="e")

        # Stop bits
        ctk.CTkLabel(self, text="Stop bits:").grid(row=2, column=1, padx=20, pady=5, sticky="w")
        self.stop_menu = ctk.CTkOptionMenu(
            self,
            values=["1", "1.5", "2"],
            width=140
        )
        self.stop_menu.grid(row=2, column=1, padx=20, pady=5, sticky="e")

        # --- Handshakes ---
        self.xonxoff_var = ctk.BooleanVar()
        self.rtscts_var = ctk.BooleanVar()  # Corrigido nome da variável interna

        self.xonxoff_check = ctk.CTkCheckBox(
            self,
            text="XON/OFF\nSoftware Handshake",
            variable=self.xonxoff_var
        )
        self.xonxoff_check.grid(row=3, column=0, columnspan=2, padx=20, pady=15, sticky="w")

        self.rtscts_check = ctk.CTkCheckBox(
            self,
            text="RTS/CTS\nHardware Handshake",
            variable=self.rtscts_var  # Corrigido aqui
        )
        self.rtscts_check.grid(row=3, column=1, columnspan=2, padx=20, pady=15, sticky="w")

        # Timeout
        ctk.CTkLabel(self, text="Recieve timeout (s):").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        self.timeout_entry = ctk.CTkEntry(self, width=140)
        self.timeout_entry.grid(row=4, column=0, padx=20, pady=5, sticky="e")

        # --- Botões de Ação ---
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=5, column=0, columnspan=2, pady=30, sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            actions_frame,
            text="❌ Cancel",
            fg_color="#b71c1c",
            hover_color="#8e0000",
            width=100,
            command=self.destroy
        )
        self.cancel_btn.pack(side="left", padx=(100, 20))

        self.ok_btn = ctk.CTkButton(
            actions_frame,
            text="✔️ OK",
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            width=100,
            command=self.save_config
        )
        self.ok_btn.pack(side="left")

        self.populate_fields()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except Exception:
                pass

    def populate_fields(self):
        self.port_menu.set(self.config_data.get("port", "COM4"))
        self.baud_menu.set(str(self.config_data.get("baudrate", 9600)))
        self.bits_menu.set(str(self.config_data.get("bytesize", 7)))

        parity_map = {"N": "NONE", "E": "EVEN", "O": "ODD", "M": "MARK", "S": "SPACE"}
        internal_parity = self.config_data.get("parity", "E")
        self.parity_menu.set(parity_map.get(internal_parity, "EVEN"))

        self.stop_menu.set(str(self.config_data.get("stopbits", 2)))
        self.timeout_entry.delete(0, "end")
        self.timeout_entry.insert(0, str(self.config_data.get("timeout", 5.0)))

        self.xonxoff_var.set(self.config_data.get("xonxoff", True))
        self.rtscts_var.set(self.config_data.get("rtscts", False))  # Corrigido de rtsxcts para rtscts

    def save_config(self):
        parity_reverse_map = {"NONE": "N", "EVEN": "E", "ODD": "O", "MARK": "M", "SPACE": "S"}

        try:
            timeout_val = float(self.timeout_entry.get())
        except ValueError:
            timeout_val = 5.0

        # Coleta os dados atualizados dos elementos da janela
        updated_data = {
            "port": self.port_menu.get(),
            "baudrate": int(self.baud_menu.get()),
            "parity": parity_reverse_map.get(self.parity_menu.get(), "E"),
            "stopbits": float(self.stop_menu.get()) if "." in self.stop_menu.get() else int(self.stop_menu.get()),
            "bytesize": int(self.bits_menu.get()),
            "timeout": timeout_val,
            "write_timeout": 5.0,
            "xonxoff": self.xonxoff_var.get(),
            "rtscts": self.rtscts_var.get()
        }

        # Salva as configurações fisicamente no arquivo serial.json
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=4)

        # Atualiza o estado e os botões da MainWindow (janela pai)
        if self.parent and hasattr(self.parent, 'controller'):
            # Força o backend a reler o JSON e reiniciar a porta serial
            self.parent.controller.reload_config()
            
            # Verifica se o backend conseguiu abrir a nova porta com sucesso
            if hasattr(self.parent.controller, 'manager') and self.parent.controller.manager.is_open:
                # Atualiza o indicador visual de status
                self.parent.status_label.configure(text="🟢 Conectado", text_color="green")
                self.parent.log(f"Configurações aplicadas. Conectado em {updated_data['port']}.")
                
                # REGRAS DE BLOQUEIO: Se está conectado, tranca o botão Conectar e Configurações
                if hasattr(self.parent, 'connect_button'):
                    self.parent.connect_button.configure(state="disabled")
                if hasattr(self.parent, 'config_button'):
                    self.parent.config_button.configure(state="disabled")
                if hasattr(self.parent, 'disconnect_button'):
                    self.parent.disconnect_button.configure(state="normal")
            else:
                # Caso a porta não consiga abrir (ex: permissão negada ou desconectada)
                self.parent.status_label.configure(text="🔴 Desconectado", text_color="red")
                self.parent.log(f"Configurações salvas para {updated_data['port']}. Clique em 'Conectar' para aplicar.")
                
                # REGRAS DE LIBERAÇÃO: Se falhou ou caiu, libera os botões para nova tentativa
                if hasattr(self.parent, 'connect_button'):
                    self.parent.connect_button.configure(state="normal")
                if hasattr(self.parent, 'config_button'):
                    self.parent.config_button.configure(state="normal")

        # Fecha a janela de configurações após salvar
        self.destroy()