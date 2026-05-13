import os
import subprocess
import sys
import threading
import customtkinter as ctk
from dotenv import load_dotenv, set_key

from core.config import VERSION
from services.whatsapp_service import enviar_boleto
from services.portal_service import executar_download

# Configurações iniciais do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"BoletoBot {VERSION} - Setup & Config")
        self.geometry("600x780")

        load_dotenv()
        self.check_playwright()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text=f"BoletoBot {VERSION}", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 5))

        self.subtitle_label = ctk.CTkLabel(self.main_frame, text="Automação de Boletos UVV", font=ctk.CTkFont(size=14))
        self.subtitle_label.grid(row=0, column=0, padx=20, pady=(45, 20))

        # Registro de validação
        vcmd_matricula = (self.register(self.validate_matricula), "%P")
        vcmd_whatsapp = (self.register(self.validate_whatsapp), "%P")

        # Campos .env
        self.matricula_entry = self.create_input("Matrícula (UVV):", os.getenv("MATRICULA", ""), 1, validate="key", validatecommand=vcmd_matricula)
        self.password_entry = self.create_input("Senha (UVV):", os.getenv("PASSWORD", ""), 2, show="*")
        self.contato_entry = self.create_input("WhatsApp (Ex: 5527999999999):", os.getenv("CONTATO", ""), 3, validate="key", validatecommand=vcmd_whatsapp)
        self.arquivo_entry = self.create_input("Pasta dos Boletos (Caminho):", os.getenv("ARQUIVO", os.path.join(os.getcwd(), "boletos")), 4)

        # Botão de Salvar
        self.save_button = ctk.CTkButton(self.main_frame, text="Salvar Configuração", command=self.save_config)
        self.save_button.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Divisor
        self.separator = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray")
        self.separator.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # Ações
        self.actions_label = ctk.CTkLabel(self.main_frame, text="Ações de Automação", font=ctk.CTkFont(size=16, weight="bold"))
        self.actions_label.grid(row=11, column=0, padx=20, pady=(10, 10))

        self.login_button = ctk.CTkButton(self.main_frame, text="Vincular WhatsApp (Scan QR Code)", fg_color="transparent", border_width=2, command=self.link_whatsapp)
        self.login_button.grid(row=12, column=0, padx=20, pady=5, sticky="ew")

        self.schedule_button = ctk.CTkButton(self.main_frame, text="Agendar no Windows (10:00 AM)", fg_color="#2ecc71", hover_color="#27ae60", command=self.schedule_task)
        self.schedule_button.grid(row=13, column=0, padx=20, pady=5, sticky="ew")

        # Console de Status
        self.status_box = ctk.CTkTextbox(self.main_frame, height=120)
        self.status_box.grid(row=14, column=0, padx=20, pady=(20, 0), sticky="nsew")
        self.log("BoletoBot iniciado. Configure seus dados acima.")

    def check_playwright(self):
        # Verifica se o executável do playwright existe ou se o navegador está instalado
        # Se estiver rodando como EXE, o sys.executable é o próprio EXE
        pass

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
        env_path = ".env"
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("")

        set_key(env_path, "MATRICULA", self.matricula_entry.get())
        set_key(env_path, "PASSWORD", self.password_entry.get())
        set_key(env_path, "CONTATO", self.contato_entry.get())
        set_key(env_path, "ARQUIVO", self.arquivo_entry.get())

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
                subprocess.run([sys.executable, "--enviar", "--visible"], check=True)
            else:
                enviar_boleto(headless=False)
            self.log("Navegador fechado.")
        except Exception as e:
            self.log(f"Erro ao abrir WhatsApp: {e}")

    def schedule_task(self):
        self.log("Agendando tarefa no Windows...")
        # Define o comando que será agendado
        if getattr(sys, 'frozen', False):
            # Se for EXE, o agendador chama o EXE com flags
            exe_path = sys.executable
            command_baixar = f'"{exe_path}" --baixar'
            command_enviar = f'"{exe_path}" --enviar'
        else:
            python_exe = sys.executable
            script_baixar = os.path.abspath("services/portal_service.py")
            script_enviar = os.path.abspath("services/whatsapp_service.py")
            command_baixar = f'"{python_exe}" "{script_baixar}"'
            command_enviar = f'"{python_exe}" "{script_enviar}"'

        # Criar script temporário de powershell para o agendador
        ps_content = f"""
$action1 = New-ScheduledTaskAction -Execute "{command_baixar.split(' ')[0].replace('"', '')}" -Argument "{' '.join(command_baixar.split(' ')[1:])}"
$action2 = New-ScheduledTaskAction -Execute "{command_enviar.split(' ')[0].replace('"', '')}" -Argument "{' '.join(command_enviar.split(' ')[1:])}"
$trigger = New-ScheduledTaskTrigger -Daily -At 10:00am
Register-ScheduledTask -Action $action1, $action2 -Trigger $trigger -TaskName "BoletoBot_Automation" -Description "Automação de Boletos UVV" -Force
"""
        ps_path = os.path.join(os.getcwd(), "scripts", "temp_scheduler.ps1")
        os.makedirs(os.path.dirname(ps_path), exist_ok=True)
        with open(ps_path, "w") as f:
            f.write(ps_content)

        try:
            subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_path], check=True, capture_output=True)
            self.log("Sucesso: Tarefa agendada para às 10:00 todos os dias!")
        except Exception as e:
            self.log(f"Erro ao agendar: {e}")

if __name__ == "__main__":
    # Lógica de Multiproc para o Executável Único
    if len(sys.argv) > 1:
        load_dotenv()
        if "--enviar" in sys.argv:
            is_headless = "--visible" not in sys.argv
            enviar_boleto(headless=is_headless)
            sys.exit(0)
        elif "--baixar" in sys.argv:
            executar_download()
            sys.exit(0)
        elif "--install-playwright" in sys.argv:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
            sys.exit(0)

    app = App()
    app.mainloop()
