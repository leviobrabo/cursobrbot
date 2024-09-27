from ..bot.bot import bot
from telebot import types
from ..database.users import UserManager
from ..config import PAYMENT_POST_ID

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
        btn_50 = types.InlineKeyboardButton('⭐️ 50 Estrelas - 1 Mês', callback_data="50_estrelas")
        btn_100 = types.InlineKeyboardButton('⭐️ 350 Estrelas - 2 Meses', callback_data="350_estrelas")
        btn_150 = types.InlineKeyboardButton('⭐️ 500 Estrelas - 3 Meses', callback_data="500_estrelas")
        btn_cancel = types.InlineKeyboardButton('Cancelar', callback_data="menu_start")
        markup.row(btn_50)
        markup.row(btn_100)
        markup.row(btn_150)
        markup.row(btn_cancel)
        photo_pay = 'https://i.imgur.com/c3nzNhd.png'  

        bot.send_photo(
            user_id,
            photo=photo_pay, 
            caption="Escolha uma das opções abaixo para renovar sua assinatura:",
            parse_mode='HTML',
            reply_markup=markup
        )

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    user = user_manager.search_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Erro: usuário não encontrado no banco de dados.")
        return

    # Defina o tempo premium com base no número de estrelas
    if payload == 'stars_50':
        months = 1
    elif payload == 'stars_350':
        months = 2
    elif payload == 'stars_500':
        months = 3
    else:
        bot.send_message(user_id, "Erro: o valor do pagamento não é válido.")
        return
    
    # Atualiza o status do usuário no banco de dados para premium
    user_manager.update_user_info(user_id, 'premium', 'true')
    
    # Calcula a data de expiração e define o initial_date
    from datetime import datetime, timedelta
    current_datetime = datetime.now()
    expiration_date = current_datetime + timedelta(days=30 * months)
    initial_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    user_manager.update_user_info(user_id, 'final_date', expiration_date.strftime('%Y-%m-%d %H:%M:%S'))
    user_manager.update_user_info(user_id, 'initial_date', initial_date)

    # Verificar se o usuário tem um indicador
    indicador_id = user.get("indicado")
    if indicador_id:
        indicador = user_manager.search_user(int(indicador_id))
        
        if indicador:
            print(indicador)
            # Obter o valor atual de indicacao
            indicacao_atual = indicador.get("indicacao", 0)  # Vamos garantir que 'indicacao' é um inteiro
            if isinstance(indicacao_atual, int):
                indicacao_atual = int(indicacao_atual)
            else:
                indicacao_atual = 0

            print(f"Indicacao atual: {indicacao_atual}")
            
            # Incrementar o valor de indicacao
            novo_valor_indicacao = indicacao_atual + 1
            print(f"Novo valor de indicacao: {novo_valor_indicacao}")
            
            # Atualiza o valor de indicacao no banco de dados
            user_manager.update_user_indicacao(int(indicador_id), novo_valor_indicacao)

            # Atualiza o final_date do indicador
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

            # Notifica o indicador sobre a indicação bem-sucedida
            bot.send_message(
                int(indicador_id), 
                "<b>Parabéns! Alguém assinou usando sua referência.</b>\n\nVocê recebeu 1 dia de acesso para assistir seus filmes.", 
                parse_mode="HTML"
            )
    
    # Mensagem de confirmação de pagamento
    photo_paid = 'https://i.imgur.com/Vcwajly.png'
    caption_sucess = f"Pagamento bem-sucedido! Você agora é premium por {months} mês(es)."
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

    # Enviar notificação de pagamento
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
