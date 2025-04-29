import os
import sys
import shutil
import subprocess
from pathlib import Path


def build_windows():
    """Сборка исполняемого файла для Windows с помощью PyInstaller"""
    print("Building Windows executable...")

    # Устанавливаем зависимости проекта для Windows из файла requirements.txt
    # sys.executable - путь к текущему интерпретатору Python
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Создаём директорию bin, если она не существует
    # exist_ok=True позволяет не выбрасывать ошибку, если директория уже существует
    bin_dir = Path("bin")
    bin_dir.mkdir(exist_ok=True)

    # Create __init__.py files in all source directories to make them proper Python packages
    create_init_files()

    # Выполняем сборку исполняемого файла с помощью PyInstaller
    # -F: создать один файл вместо директории
    # -w: запускать в оконном режиме (не показывать консоль)
    # --icon: путь к иконке приложения
    # -n: имя выходного файла
    # --add-data: добавить дополнительные файлы/директории в сборку

    # Если файл PyInstaller спецификации существует, используем его
    spec_file = Path("aichat.spec")
    if spec_file.exists():
        subprocess.run([sys.executable, "-m", "PyInstaller", "aichat.spec"])
    else:
        # Создаем новый файл спецификации
        subprocess.run([sys.executable, "-m", "PyInstaller", "-F", "-w", "--icon=assets/icon.ico", "-n", "aichat", "src/main.py"])

    # Если сборка прошла успешно, копируем исполняемый файл в директорию bin
    # shutil.copy2 - копирует файл с сохранением метаданных (даты создания и т.д.)
    dist_file = Path("dist/aichat.exe")
    if dist_file.exists():
        shutil.copy2(dist_file, bin_dir / "aichat.exe")
        print("Windows build completed! Executable location: bin/aichat.exe")
    else:
        print("Error: Windows build failed.")


def build_linux():
    """Сборка исполняемого файла для Linux с помощью PyInstaller"""
    print("Building Linux executable...")

    # Устанавливаем зависимости проекта для Linux из файла requirements.txt
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Создаём директорию bin, если она не существует
    bin_dir = Path("bin")
    bin_dir.mkdir(exist_ok=True)

    # Create __init__.py files in all source directories to make them proper Python packages
    create_init_files()

    # Выполняем сборку исполняемого файла с помощью PyInstaller
    # -F: создать один файл вместо директории
    # -w: запускать в оконном режиме (не показывать консоль)
    # --icon: путь к иконке приложения
    # -n: имя выходного файла

    # Если файл PyInstaller спецификации существует, используем его
    spec_file = Path("aichat.spec")
    if spec_file.exists():
        subprocess.run([sys.executable, "-m", "PyInstaller", "aichat.spec"])
    else:
        # Создаем новый файл спецификации
        subprocess.run([sys.executable, "-m", "PyInstaller", "-F", "-w", "--icon=assets/icon.ico", "-n", "aichat", "src/main.py"])

    # Если сборка прошла успешно, копируем исполняемый файл в директорию bin
    dist_file = Path("dist/aichat")
    if dist_file.exists():
        shutil.copy2(dist_file, bin_dir / "aichat")
        print("Linux build completed! Executable location: bin/aichat")
    else:
        print("Error: Linux build failed.")


def create_init_files():
    """Create __init__.py files in source directories to make them proper Python packages"""
    # Create __init__.py in src directory
    src_dir = Path("src")
    init_file = src_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w') as f:
            pass  # Create an empty file

    # Create __init__.py in api directory
    api_dir = src_dir / "api"
    init_file = api_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w') as f:
            pass  # Create an empty file

    # Create __init__.py in ui directory
    ui_dir = src_dir / "ui"
    init_file = ui_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w') as f:
            pass  # Create an empty file

    # Create __init__.py in utils directory
    utils_dir = src_dir / "utils"
    init_file = utils_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w') as f:
            pass  # Create an empty file


def main():
    """Выбор сборки в зависимости от операционной системы"""
    # Определяем операционную систему на которой запущен скрипт
    if sys.platform == "win32":
        build_windows()
    elif sys.platform == "linux" or sys.platform == "linux2":
        build_linux()
    else:
        print(f"Error: Unsupported platform {sys.platform}")


if __name__ == "__main__":
    main()
