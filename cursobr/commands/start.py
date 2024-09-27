from telebot import types
from ..bot.bot import bot
from ..config import GROUP_LOG_ID
from ..database.users import UserManager
from ..database.cursos import VideoManager
import logging

user_manager = UserManager()
video_manager = VideoManager()

@bot.message_handler(commands=["start"])
def cmd_start(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        user_id = message.from_user.id
        first_name = message.from_user.first_name

        user = user_manager.search_user(user_id)

        if not user:
            if message.text.startswith('/start '):
                cmd_arg = message.text[7:].strip()
                if cmd_arg == 'how_to_use':
                    bot.reply_to(
                        message,
                        "Para saber como pesquisar, visite: https://telegra.ph/Como-utilizar-filtros-09-22"
                    )
                    return
                else:
                    indicador_id = cmd_arg
                    user_manager.add_user_db(message)
                    user = user_manager.search_user(user_id)
                    user_manager.update_user_indicado(user_id, indicador_id)
                    user_manager.update_user_indicacao(int(indicador_id))
                    bot.send_message(
                        indicador_id,
                        f"👨‍💻Olá, venho lhe avisar que {first_name} iniciou o bot utilizando seu link de referência."
                    )
                    logging.info(f"O usuário {user_id} foi indicado por {indicador_id}.")
            else:
                user_manager.add_user_db(message)
                user = user_manager.search_user(user_id)

            user_info = (
                f"<b>#{bot.get_me().username} #New_User</b>\n"
                f"<b>User:</b> {user['first_name']}\n"
                f"<b>ID:</b> <code>{user['user_id']}</code>\n"
                f"<b>Username:</b> @{user.get('username', 'Sem Username')}"
            )
            bot.send_message(GROUP_LOG_ID, user_info, message_thread_id=43147)
            logging.info(f'Novo usuário ID: {user["user_id"]} foi criado no banco de dados')

        else:
            if message.text.startswith('/start '):
                cmd_arg = message.text[7:].strip()
                if cmd_arg == 'how_to_use':
                    bot.reply_to(
                        message,
                        "Para saber como pesquisar, visite: https://telegra.ph/Como-utilizar-filtros-09-22"
                    )
                    return

        markup = types.InlineKeyboardMarkup()
        pesquisar = types.InlineKeyboardButton(
            "🔎 | Pesquisar", switch_inline_query_current_chat=''
        )
        channel_ofc = types.InlineKeyboardButton(
            "📢 Canal Oficial", url="https://t.me/cursobroff"
        )
        assinatura = types.InlineKeyboardButton(
            text='🎫 Assinatura', callback_data='comprar'
        )
        historico = types.InlineKeyboardButton(
            text='💾 Histórico', switch_inline_query_current_chat='HISTORICO'
        )
        categoria = types.InlineKeyboardButton(
            text='📈 Categoria', callback_data='categoria'
        )
        how_to_use = types.InlineKeyboardButton(
            text='🆕 Novidades', url='https://t.me/novidade_cursobr'
        )
        indicacao = types.InlineKeyboardButton(
            text='🤝 Indicação', callback_data='indique'
        )
        config_pv = types.InlineKeyboardButton(
            "🪪 Sua conta", callback_data="config"
        )

        markup.add(pesquisar)
        markup.add(historico, channel_ofc)
        markup.add(assinatura, how_to_use)
        markup.add(indicacao, categoria)
        markup.add(config_pv)

        photo = "https://i.imgur.com/q16rY8x.png"
        final_date = user.get("final_date", "")
        indicado = user.get("indicado", "")

        if final_date:
            expiracao_texto = f"<b>• Expiração:</b> <code>{final_date}</code>\n\n"
        else:
            expiracao_texto = "<b>• Expiração:</b> <code>Sem assinatura ativa</code>\n\n"

        if indicado:
            conta_vinculada_texto = f"<b>• Conta vinculada:</b> <code>{indicado}</code>\n"
        else:
            conta_vinculada_texto = "<b>• Conta vinculada:</b> <code>Não tem</code>\n"

        total_videos = video_manager.count_unique_idnt()
        category_list_text = f"<b>• Cursos:</b> {total_videos}"

        msg_start = (
            f"Olá, <b>{first_name}</b>!\n\n"
            f"Eu sou <b>{bot.get_me().first_name}</b>. Use os menus abaixo para interagir com o bot. "
            f"Tenho inúmeros cursos para você acessar facilmente.\n\n"
            f"<b><u>Informações</u></b>\n"
            f"{conta_vinculada_texto}"
            f"{expiracao_texto}"
            f"<b><u>Catálogo</u></b>\n"
            f"{category_list_text}\n\n"
            f"<b><u>Ajuda</u></b>\n"
            f"<a href='https://telegra.ph/Como-utilizar-filtros-09-22'>• Como pesquisar?</a>\n"
            f"<a href='https://t.me/kylorensbot'>• Falar com o suporte</a>"
        )

        bot.send_photo(
            message.chat.id,
            photo=photo,
            caption=msg_start,
            reply_markup=markup,
            parse_mode='HTML'
        )

    except Exception as e:
        logging.error(f"Erro ao enviar o start: {e}")