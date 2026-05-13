import subprocess
import sys


def build():
    print("Iniciando processo de build do BoletoBot...")

    from core.config import VERSION

    # Nome do executável final
    exe_name = f"BoletoBot_{VERSION}"

    # Comando PyInstaller
    # --onefile: Gera um único arquivo .exe
    # --windowed: Não abre o console ao iniciar (apenas GUI)
    # --collect-all customtkinter: Garante que os temas e arquivos do CustomTkinter sejam incluídos
    # --add-data: Adiciona arquivos extras que o programa precisa

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        "--collect-all=customtkinter",
        "--add-data=core;core",
        "--add-data=pages;pages",
        "--add-data=services;services",
        "--add-data=.env.example;.",
        "configurator.py",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 40)
        print(f"SUCESSO! O executável foi gerado na pasta 'dist'.")
        print(f"Você pode enviar o arquivo '{exe_name}.exe' para qualquer pessoa.")
        print("=" * 40)
    except subprocess.CalledProcessError as e:
        print(f"\nERRO durante o build: {e}")


if __name__ == "__main__":
    build()
