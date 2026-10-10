import base64
import os
import subprocess
import sys
import threading
import customtkinter as ctk
from dotenv import set_key

from core.config import BASE_DIR, CAMINHO_BOLETOS, ENV_PATH, VERSION
from main import main as executar_rotina
from services.whatsapp_service import abrir_para_autenticacao

# Configurações iniciais do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"BoletoBot {VERSION} - Setup & Config")
        self.geometry("600x780")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text="Automação de Boletos UVV", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(45, 20))

        # ═══ Campos de Configuração ═══
        # Registro de validação
        vcmd_matricula = (self.register(self.validate_matricula), "%P")
        vcmd_whatsapp = (self.register(self.validate_whatsapp), "%P")

        # Campos .env
        self.matricula_entry = self.create_input("Matrícula (UVV):", os.getenv("MATRICULA", ""), 1, validate="key", validatecommand=vcmd_matricula)
        self.password_entry = self.create_input("Senha (UVV):", os.getenv("PASSWORD", ""), 2, show="*")
        self.contato_entry = self.create_input("WhatsApp (Ex: 5527999999999):", os.getenv("CONTATO", ""), 3, validate="key", validatecommand=vcmd_whatsapp)
        self.arquivo_entry = self.create_input("Pasta dos Boletos (Caminho):", CAMINHO_BOLETOS, 4)

        # Botão de Salvar
        self.save_button = ctk.CTkButton(self.main_frame, text="Salvar Configuração", command=self.save_config)
        self.save_button.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Divisor
        self.separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray")
        self.separator.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # ═══ Botões de Ação ═══
        self.actions_label = ctk.CTkLabel(self.main_frame, text="Ações de Automação", font=ctk.CTkFont(size=16, weight="bold"))
        self.actions_label.grid(row=11, column=0, padx=20, pady=(10, 10))

        self.login_button = ctk.CTkButton(self.main_frame, text="Vincular WhatsApp (Scan QR Code)", fg_color="transparent", border_width=2, command=self.link_whatsapp)
        self.login_button.grid(row=12, column=0, padx=20, pady=5, sticky="ew")

        self.schedule_button = ctk.CTkButton(self.main_frame, text="Agendar no Windows (10:00 AM)", fg_color="#2ecc71", hover_color="#27ae60", command=self.schedule_task)
        self.schedule_button.grid(row=13, column=0, padx=20, pady=5, sticky="ew")

        # ═══ Console de Status ═══
        self.status_box = ctk.CTkTextbox(self.main_frame, height=120)
        self.status_box.grid(row=14, column=0, padx=20, pady=(20, 0), sticky="nsew")
        self.log("BoletoBot iniciado. Configure seus dados acima.")
        
        # Iniciar verificação do playwright no background agora que a UI está pronta
        self.check_playwright()

    def check_playwright(self):
        self.log("Verificando/Instalando navegador Chromium (Pode demorar na 1ª vez)...")
        threading.Thread(target=self._install_playwright_bg, daemon=True).start()

    def _install_playwright_bg(self):
        try:
            from playwright._impl._driver import compute_driver_executable, get_driver_env
            driver_executable, driver_cli = compute_driver_executable()
            env = get_driver_env()
            if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
                env["PLAYWRIGHT_BROWSERS_PATH"] = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
            
            # Executa silenciosamente no background (esconde a janela preta no Windows)
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run([driver_executable, driver_cli, "install", "chromium"], env=env, check=True, creationflags=creationflags)
            self.after(0, lambda: self.log("✅ Navegador pronto para uso!"))
        except Exception as e:
            self.after(0, lambda: self.log(f"⚠️ Erro ao instalar navegador: {e}"))

    def validate_matricula(self, P):
        if P == "" or (P.isdigit() and len(P) <= 9):
            return True
        return False

    def validate_whatsapp(self, P):
        if P == "" or (P.isdigit() and len(P) <= 13):
            return True
        return False

    def create_input(self, label_text, initial_value, row, show=None, **kwargs):
        label = ctk.CTkLabel(self.main_frame, text=label_text)
        label.grid(row=row*2-1, column=0, padx=20, pady=(5, 0), sticky="w")
        entry = ctk.CTkEntry(self.main_frame, placeholder_text=label_text, show=show, **kwargs)
        entry.grid(row=row*2, column=0, padx=20, pady=(0, 10), sticky="ew")
        entry.insert(0, initial_value)
        return entry

    def log(self, message):
        self.status_box.insert("end", f"> {message}\n")
        self.status_box.see("end")

    def save_config(self):
        if not os.path.exists(ENV_PATH):
            with open(ENV_PATH, "w") as f:
                f.write("")

        set_key(ENV_PATH, "MATRICULA", self.matricula_entry.get())
        set_key(ENV_PATH, "PASSWORD", self.password_entry.get())
        set_key(ENV_PATH, "CONTATO", self.contato_entry.get())
        set_key(ENV_PATH, "ARQUIVO", self.arquivo_entry.get())

        self.log("Configurações salvas no arquivo .env!")

    def link_whatsapp(self):
        self.log("Abrindo navegador para scan do QR Code...")
        # Executa em uma thread para não travar a UI
        thread = threading.Thread(target=self._run_whatsapp_link)
        thread.start()

    def _run_whatsapp_link(self):
        try:
            # Se estivermos em um EXE, chamamos a nós mesmos com a flag
            if getattr(sys, 'frozen', False):
                subprocess.run([sys.executable, "--vincular"], check=True)
            else:
                abrir_para_autenticacao()
            self.log("Navegador fechado.")
        except Exception as e:
            self.log(f"Erro ao abrir WhatsApp: {e}")

    def schedule_task(self):
        self.log("Agendando tarefa no Windows...")
        if getattr(sys, 'frozen', False):
            executavel, argumentos = sys.executable, "--executar"
        else:
            executavel = sys.executable
            argumentos = f'"{os.path.join(BASE_DIR, "main.py")}"'

        script = self._gerar_script_agendamento(executavel, argumentos)
        # -EncodedCommand evita problemas de aspas/espaços nos caminhos
        script_codificado = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        resultado = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", script_codificado],
            capture_output=True, text=True,
        )
        if resultado.returncode == 0:
            self.log("Sucesso: Tarefa agendada para às 10:00 todos os dias!")
        else:
            self.log(f"Erro ao agendar: {resultado.stderr.strip()}")

    @staticmethod
    def _gerar_script_agendamento(executavel: str, argumentos: str) -> str:
        def literal(valor: str) -> str:
            return "'" + valor.replace("'", "''") + "'"

        return f"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Remove a tarefa das versões anteriores do configurador, que tinha outro nome
Unregister-ScheduledTask -TaskName 'BoletoBot_Automation' -Confirm:$false -ErrorAction SilentlyContinue
$action = New-ScheduledTaskAction -Execute {literal(executavel)} -Argument {literal(argumentos)} -WorkingDirectory {literal(BASE_DIR)}
$trigger = New-ScheduledTaskTrigger -Daily -At 10:00am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'BoletoBot_Daily' -Action $action -Trigger $trigger -Settings $settings -Description 'Automação de Boletos UVV (BoletoBot)' -Force | Out-Null
"""

if __name__ == "__main__":
    # Lógica de Multiproc para o Executável Único
    if len(sys.argv) > 1:
        if "--vincular" in sys.argv:
            abrir_para_autenticacao()
            sys.exit(0)
        elif "--executar" in sys.argv:
            executar_rotina()
        elif "--install-playwright" in sys.argv:
            from playwright._impl._driver import compute_driver_executable, get_driver_env
            driver_executable, driver_cli = compute_driver_executable()
            env = get_driver_env()
            if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
                env["PLAYWRIGHT_BROWSERS_PATH"] = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
            subprocess.run([driver_executable, driver_cli, "install", "chromium"], env=env)
            sys.exit(0)

    app = App()
    app.mainloop()
