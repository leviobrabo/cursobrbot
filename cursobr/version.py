from sys import version_info

import telebot

python_version = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
cursosbrbot_version = "0.0.1"
telebot_version = (
    telebot.__version__ if hasattr(telebot, "__version__") else "Versão não encontrada"
)