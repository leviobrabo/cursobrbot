from ..bot.bot import bot
from telebot import types
from ..database.users import UserManager
from ..config import PAYMENT_POST_ID
import logging
user_manager = UserManager()

@bot.message_handler(commands=["renovar_assinatura"])
def renovar_assinatura(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = message.from_user.id

    user = user_manager.search_user(user_id)
    if user.get('premium') == 'true':
        back_to_home = types.InlineKeyboardButton(
                '↩️ Voltar', callback_data='menu_start'
                )
        markup.add(back_to_home)
        photo_sub = 'https://i.imgur.com/bngnGuN.png'
        bot.send_photo(user_id, photo=photo_sub, caption="Você já é um usuário premium.")
        markup = types.InlineKeyboardMarkup()
    else:     
        markup = types.InlineKeyboardMarkup()
        btn_50 = types.InlineKeyboardButton('⭐️ 100 Estrelas - 1 Mês', callback_data="100_estrelas")
        btn_100 = types.InlineKeyboardButton('⭐️ 200 Estrelas - 2 Meses', callback_data="200_estrelas")
        btn_150 = types.InlineKeyboardButton('⭐️ 350 Estrelas - 3 Meses', callback_data="350_estrelas")
        btn_termo = types.InlineKeyboardButton('📁 Termo de uso', url='https://telegra.ph/Termo-de-uso-09-28')
        btn_cancel = types.InlineKeyboardButton('Cancelar', callback_data="menu_start")
        markup.row(btn_50)
        markup.row(btn_100)
        markup.row(btn_150)
        markup.row(btn_termo)
        markup.row(btn_cancel)
        photo_pay = 'https://i.imgur.com/c3nzNhd.png'  

        caption_nws = (
                    "⭐️ <b>Escolha seu plano de assinatura:</b>\n\n"
                    "Com a assinatura premium, você terá acesso ilimitado a todos os cursos, "
                    "suporte prioritário e a possibilidade de favoritar seus cursos preferidos. "
                    "Além disso, seu pagamento é feito de maneira anônima com estrelas do Telegram!\n\n"
                    "<blockquote>⭐️ 100 ≈ US$ 1,84</blockquote>"
                )
        bot.send_photo(
            user_id,
            photo=photo_pay, 
            caption=caption_nws,
            parse_mode='HTML',
            reply_markup=markup
        )

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    user = user_manager.search_user(user_id)
    
    if not user:
        logging.error(user_id, "Erro: usuário não encontrado no banco de dados.")
        return

    if payload == 'stars_100':
        months = 1
        payload_text = '100 estrela'
    elif payload == 'stars_200':
        months = 2
        payload_text = '200 estrelas'
    elif payload == 'stars_350':
        months = 3
        payload_text = '350 estrelas'
    else:
        bot.send_message(user_id, "Erro: o valor do pagamento não é válido.")
        return
    
    user_manager.update_user_info(user_id, 'premium', 'true')
    
    from datetime import datetime, timedelta
    current_datetime = datetime.now()
    expiration_date = current_datetime + timedelta(days=30 * months)
    initial_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    user_manager.update_user_info(user_id, 'final_date', expiration_date.strftime('%Y-%m-%d %H:%M:%S'))
    user_manager.update_user_info(user_id, 'initial_date', initial_date)

    indicador_id = user.get("indicado")
    if indicador_id:
        indicador = user_manager.search_user(int(indicador_id))
        
        if indicador:
            indicacao_atual = indicador.get("indicacao", 0)  
            if isinstance(indicacao_atual, int):
                indicacao_atual = int(indicacao_atual)
            else:
                indicacao_atual = 0
            
            novo_valor_indicacao = indicacao_atual + 1
            
            user_manager.update_user_indicacao(int(indicador_id), novo_valor_indicacao)

            final_date = indicador.get("final_date")
            if not final_date:
                initial_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Salvar com horas
                new_date_obj = datetime.now() + timedelta(days=1)
                final_date = new_date_obj.strftime('%Y-%m-%d %H:%M:%S')  # Salvar com horas
                user_manager.update_user_info(int(indicador_id), "initial_date", initial_date)
                user_manager.update_user_info(int(indicador_id), "final_date", final_date)
                user_manager.update_user_info(int(indicador_id), 'premium', 'true')
            else:
                current_final_date_obj = datetime.strptime(final_date, '%Y-%m-%d %H:%M:%S')
                new_date_obj = current_final_date_obj + timedelta(days=1)
                final_date = new_date_obj.strftime('%Y-%m-%d %H:%M:%S')
                user_manager.update_user_info(int(indicador_id), "final_date", final_date)
                user_manager.update_user_info(int(indicador_id), 'premium', 'true')

            bonus_message = (
                    "<b>🎉 Parabéns! Alguém assinou usando seu link de indicação.</b>\n\n"
                    "Você ganhou <b>1 dia de acesso premium</b> como recompensa! Agora você pode continuar aproveitando "
                    "todos os nossos cursos sem limites. Continue compartilhando e indique mais amigos para ganhar ainda mais dias grátis!\n\n"
                    f"📅 <b>Seu novo prazo de expiração:</b> {final_date}."
                )
            bot.send_message(
                int(indicador_id), 
                bonus_message, 
                parse_mode="HTML"
            )
    
    photo_paid = 'https://i.imgur.com/Vcwajly.png'
    caption_sucess = (
            f"🎉 <b>Pagamento bem-sucedido!</b>\n\n"
            f"Você adquiriu <b>{payload_text}</b> para {months} mês(es) de acesso premium ao Curso Bot.\n"
            "Agora você tem acesso ilimitado a todos os nossos cursos, com suporte prioritário e a possibilidade de favoritar seus cursos preferidos.\n\n"
            f"📅 <b>Seu acesso premium expira em:</b> {expiration_date.strftime('%d/%m/%Y')}\n\n"
            "Aproveite sua jornada de aprendizado e, se precisar de algo, estamos aqui para ajudar! 😉"
        )
    markup = types.InlineKeyboardMarkup()
    back_to_home = types.InlineKeyboardButton(
                '↩️ Voltar', callback_data='menu_start'
            )
    markup.add(back_to_home)
    bot.send_photo(
        chat_id=message.from_user.id,
        photo=photo_paid,
        caption=caption_sucess,
        parse_mode='HTML',
        reply_markup=markup,
    )

    user_info = (
        f"<b>#{bot.get_me().username} #Pagamento</b>\n"
        f"<b>User:</b> {user.get('first_name', 'Usuário Desconhecido')}\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> @{user.get('username', 'Sem Username')}\n"
        f"<b>Valor:</b> {payload}\n"
        f"<b>Período:</b> {months} mês(es)"
    )
    bot.send_message(PAYMENT_POST_ID, user_info)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True,
        error_message='Erro. Tente novamente mais tarde.'
    )
