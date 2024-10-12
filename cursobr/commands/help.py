from telebot import types

from ..bot.bot import bot
from ..config import *
from ..database.users import UserManager
import logging

user_manager = UserManager
@bot.message_handler(commands=["help"])
def cmd_help(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        if message.chat.type == "private":

            text = (
                f"Olá! Eu sou um bot cheio de cursos para você assistir."
                f"\n\nAlém disso, tenho comandos para facilitar sua busca e uso do bot. Fique à vontade para interagir comigo e descobrir mais sobre o mundo que nos cerca!" 
                f"\n\n<b>Basta clicar em um deles:</b>"
            )

            markup = types.InlineKeyboardMarkup()
            commands = types.InlineKeyboardButton(
                "Lista de comandos", callback_data="commands"
            )
            suppport = types.InlineKeyboardButton("Suporte", url="https://t.me/updatehist")
            doacao = types.InlineKeyboardButton(
                "💰 Doações", callback_data="doacao"
            )

            markup.add(commands)
            markup.add(suppport, doacao)

            with open('cursobr/assets/q16rY8x.png', 'rb') as photo_file:
                bot.send_photo(
                    message.chat.id,
                    photo=photo_file,
                    caption=text,
                    reply_markup=markup,
                )
    except Exception as e:
        logging.error(f"Erro ao enviar o help: {e}")