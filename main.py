from cursobr.bot.bot import bot  
from telebot import util, types
from cursobr.config import GROUP_LOG_ID, PAYMENT_POST_ID, BOT_OWNER_ID, TOKEN_MERCADOPAGO
from cursobr.version import cursosbrbot_version, python_version, telebot_version
from cursobr.commands import start
from cursobr.commands import help
from cursobr.commands import ban
from cursobr.commands import sudo
from cursobr.commands import renv_assint
from cursobr.utils import get_video
from cursobr.handlers import botao
from cursobr.database.users import UserManager
from cursobr.database.cursos import VideoManager
from cursobr.database.votes import VoteManager
import telebot
import threading
from datetime import datetime, timedelta
import time
import re
import schedule
import random
from typing import List, Dict
from cursobr.loggers import logging
import mercadopago
import base64
from PIL import Image
from io import BytesIO

user_manager = UserManager()
video_manager = VideoManager()
vote_manager = VoteManager()

sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)
pending_payments = {}

# Definindo as mensagens divididas em três partes
msg_text_1 = (
    "<b>📚 Está cansado de perder tempo procurando cursos em canais? Conheça o Curso Bot!</b>\n\n"
    "⭐ <b>Por que o bot é melhor que canais tradicionais?</b> ⭐\n\n"
    "Muitos usuários enfrentam problemas ao tentar acessar cursos por meio de canais. Esses canais são frequentemente denunciados, caindo de forma inesperada, "
    "o que faz você perder o acesso ao conteúdo. Além disso, é muito fácil se perder entre diversos grupos e canais, sem uma forma clara de organização. "
    "Você também pode esquecer onde parou no último curso, ou pior, acabar se confundindo entre materiais de diferentes canais.\n\n"
    "Outro problema é que, em canais, não existe uma forma simples de guardar o conteúdo para assistir depois. Para encontrar um curso específico, "
    "você precisa navegar por longas listas de mensagens, o que consome tempo e energia. Ter que ingressar em diversos grupos para conseguir diferentes "
    "cursos só complica ainda mais, sem contar que muitos canais são desorganizados e de difícil navegação."
)

msg_text_2 = (
    "<b>🎓 As vantagens de usar o Curso Bot (@cursobrbot)</b>\n\n"
    "• <b>Histórico de Assistidos:</b> Com o Curso Bot, você nunca mais vai se perder. Ele salva automaticamente o histórico de assistidos, permitindo que você saiba "
    "exatamente onde parou em cada curso. Simples e prático.\n\n"
    "• <b>Favoritar Cursos:</b> Encontrou um curso interessante, mas não tem tempo agora? Sem problemas! Marque-o como favorito e acesse quando quiser, sem precisar "
    "procurar por ele novamente. Tudo a um clique de distância.\n\n"
    "• <b>Assinatura com Custo Baixo:</b> O bot oferece planos acessíveis para todos os bolsos, permitindo que você tenha acesso a uma variedade de cursos "
    "sem pesar no orçamento. Além disso, o pagamento é feito de forma totalmente anônima, utilizando as estrelas do próprio Telegram. Basta enviar as estrelas e pronto!"
)

msg_text_3 = (
    "• <b>Reembolso Garantido:</b> Caso tenha qualquer problema com a sua assinatura, o reembolso é garantido e processado diretamente pelo Telegram, sem complicações.\n\n"
    "• <b>Busca Avançada:</b> Precisa encontrar um curso específico? O Curso Bot oferece uma busca profunda, que permite filtrar por letra, ano ou categoria. "
    "Isso facilita a localização do conteúdo que você deseja, de forma rápida e eficiente.\n\n"
    "• <b>Sistema de Indicação:</b> Quer acesso gratuito? Basta indicar amigos! Se alguém assinar com seu link de indicação, você ganha acesso ao bot de forma "
    "gratuita. Fácil e vantajoso!\n\n"
    "• <b>Interface Simples e Suporte:</b> O layout do bot é direto e fácil de usar, com tutoriais detalhados para orientar seu uso. E se precisar de ajuda, "
    "há suporte disponível para responder suas dúvidas e atender pedidos.\n\n"
    "🌟 <b>Não perca tempo!</b> Acesse seus cursos favoritos de forma organizada e prática com o Curso Bot. Assine agora e tenha todo o conteúdo ao seu alcance, "
    "de forma rápida e segura. 🌟"
)

# Função para criar pagamento via PIX
def create_payment(value, plan_type, duration):
    expire = datetime.now() + timedelta(days=1)
    expire = expire.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")

    payment_data = {
        "transaction_amount": float(value),
        "payment_method_id": 'pix',
        "description": f"{plan_type}:{duration}",
        "installments": 1,
        "description": 'Descrição',
        "date_of_expiration": expire,
        "payer": {
            "email": 'carlosjunior20313@gmail.com'  
        }
    }
    result = sdk.payment().create(payment_data)
    return result

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data.startswith('menu_start'):
            if call.message.chat.type != 'private':
                return
            user_id = call.from_user.id
            first_name = call.from_user.first_name
            user = user_manager.search_user(user_id)

            if not user:
                user_manager.add_user_db(call.message)
                user = user_manager.search_user(user_id)
                user_info = (
                    f"<b>#{bot.get_me().username} #New_User</b>\n"
                    f"<b>User:</b> {user.get('first_name', 'Usuário Desconhecido')}\n"
                    f"<b>ID:</b> <code>{user['user_id']}</code>\n"
                    f"<b>Username:</b> @{user.get('username', 'Sem Username')}"
                )
                bot.send_message(GROUP_LOG_ID, user_info, message_thread_id=43147)

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
                text='ℹ️ Mais informações', callback_data='more'
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
            final_date_str = user.get("final_date", "")
            indicado = user.get("indicado", "")
            current_datetime = datetime.now()

            if final_date_str:
                try:
                    final_datetime = datetime.strptime(final_date_str, '%Y-%m-%d %H:%M:%S')
                    
                    time_diff = final_datetime - current_datetime
                    
                    if time_diff.total_seconds() <= 0:
                        expiracao_texto = "<b>• Expiração:</b> <code>Assinatura Expirada</code>\n\n"
                    else:
                        days = time_diff.days
                        seconds = time_diff.seconds
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        seconds = seconds % 60
                        
                        if days > 0:
                            expiracao_texto = f"<b>• Expiração:</b> Faltam <code>{days} dia{'s' if days != 1 else ''}</code> para expirar.\n\n"
                        elif hours > 0:
                            expiracao_texto = f"<b>• Expiração:</b> Faltam <code>{hours} hora{'s' if hours != 1 else ''}</code> para expirar.\n\n"
                        elif minutes > 0:
                            expiracao_texto = f"<b>• Expiração:</b> Faltam <code>{minutes} minuto{'s' if minutes != 1 else ''}</code> para expirar.\n\n"
                        else:
                            expiracao_texto = f"<b>• Expiração:</b> Faltam <code>{seconds} segundo{'s' if seconds != 1 else ''}</code> para expirar.\n\n"
                except ValueError:
                    expiracao_texto = "<b>• Expiração:</b> <code>Formato de data inválido</code>\n\n"
            else:
                expiracao_texto = "<b>• Expiração:</b> <code>Sem assinatura ativa</code>\n\n"

            if indicado:
                conta_vinculada_texto = f"<b>• Conta vinculada:</b> <code>{indicado}</code>\n"
            else:
                conta_vinculada_texto = "<b>• Conta vinculada:</b> <code>Você não é vinculado a nenhuma conta</code>\n"

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


            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo, caption=msg_start, parse_mode='HTML'
                ),
                reply_markup=markup,
            )
        elif call.data.startswith('menu_help'):
            if call.message.chat.type != 'private':
                return
            user_id = call.message.from_user.id
            user = user_manager.search_user(user_id)

            text = (
               f"Olá! Eu sou um bot cheio de cursos para você assistir."
               f"\n\nAlém disso, tenho comandos para facilitar sua busca e uso do bot. Fique à vontade para interagir comigo e descobrir mais sobre o mundo que nos cerca!" 
               f"\n\n<b>Basta clicar em um deles:</b>"
            )
            markup = types.InlineKeyboardMarkup()
            commands = types.InlineKeyboardButton(
            "Lista de comandos", callback_data="commands"
            )
            suppport = types.InlineKeyboardButton("Suporte", url="https://t.me/kylorensbot")
            doacao = types.InlineKeyboardButton(
                "💰 Doações", callback_data="doacao"
            )

            markup.add(commands)
            markup.add(suppport, doacao)

            photo = "https://i.imgur.com/q16rY8x.png"
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo, caption=text, parse_mode='HTML'
                ),
                reply_markup=markup,
            )
        elif call.data.startswith('comprar'):
            try:
                user_id = call.from_user.id
                user = user_manager.search_user(user_id)
                is_premium = user.get('premium') == 'true'
                  
                
                photo_sub = 'https://i.imgur.com/bngnGuN.png'
                if is_premium:
                    markup = types.InlineKeyboardMarkup()
                    back_to_home = types.InlineKeyboardButton(
                    '↩️ Voltar', callback_data='menu_start'
                    )
                    markup.add(back_to_home)

                    final_date = datetime.strptime(user.get('final_date'), '%Y-%m-%d %H:%M:%S')
                    days_left = (final_date - datetime.now()).days
            

                    caption_sub = (
                        "<b>🎉 Parabéns! Você já é um assinante premium.</b>\n\n"
                        "💎 <b>Assinatura ativa:</b> Você tem acesso total aos cursos e funcionalidades do bot.\n"
                        f"📅 <b>Data de Expiração:</b> {user.get('final_date')}\n"
                        f"⏳ <b>Tempo restante:</b> {days_left} dias até a expiração da sua assinatura.\n\n"
                        "Caso deseje renovar ou alterar seu plano, basta escolher uma das opções abaixo."
                    )
                    bot.edit_message_media(
                    chat_id=call.from_user.id,
                    message_id=call.message.message_id,
                    media=types.InputMediaPhoto(
                        media=photo_sub, caption=caption_sub, parse_mode='HTML'
                    ),
                    reply_markup=markup,

                )
                else:
                    markup_cmp = types.InlineKeyboardMarkup()
                    btn_comprar_estrela = types.InlineKeyboardButton(
                        '💫 Comprar com Estrelas', callback_data='estrela'
                    )
                    btn_comprar_pix = types.InlineKeyboardButton(
                        '💵 Pagar com PIX', callback_data='pix'
                    )
                    back_to_home = types.InlineKeyboardButton(
                        '↩️ Voltar', callback_data='menu_start'
                    )
                    markup_cmp.add(btn_comprar_estrela, btn_comprar_pix)
                    markup_cmp.add(back_to_home)

                    msg_text_cmp = (
                        "<b>💎 Escolha sua forma de pagamento:</b>\n\n"
                        "Você pode escolher entre pagar via PIX ou através das "
                        "<a href='https://t.me/TelegramTipsBR/329'>Estrelas do Telegram</a>.\n\n"
                        "💫 <b>Estrelas do Telegram:</b> As estrelas são usadas para desbloquear conteúdo exclusivo e suportar o projeto diretamente no Telegram.\n\n"
                        "💵 <b>PIX:</b> Pague diretamente com PIX para uma experiência rápida e segura."
                    )

                    photo_cmp = 'https://i.imgur.com/5TgYbot.png'
                    
                    bot.edit_message_media(
                            chat_id=call.from_user.id,
                            message_id=call.message.message_id,
                            media=types.InputMediaPhoto(
                                media=photo_cmp, caption=msg_text_cmp+ " ", parse_mode='HTML'
                            ),
                            reply_markup=markup_cmp,
                        )
            except Exception as e:
                logging.error(f'Erro ao gerar pagamento: {e}')
        elif call.data.startswith('pix'):
            try:
                user_id = call.from_user.id
                user = user_manager.search_user(user_id)
                markup_pix = types.InlineKeyboardMarkup()
                markup_pix.add(types.InlineKeyboardButton('1 mês - R$5,00', callback_data='plan_1_month'))
                markup_pix.add(types.InlineKeyboardButton('2 meses - R$10,00', callback_data='plan_2_months'))
                markup_pix.add(types.InlineKeyboardButton('3 meses - R$18,00', callback_data='plan_3_months'))
                markup_pix.add(types.InlineKeyboardButton(
                        '↩️ Voltar', callback_data='comprar'
                    ))
                photo_pix = 'https://i.imgur.com/ddn7f4N.png'
                txt_pix = "Escolha seu plano de assinatura:"
                bot.edit_message_media(
                            chat_id=call.from_user.id,
                            message_id=call.message.message_id,
                            media=types.InputMediaPhoto(
                                media=photo_pix, caption=txt_pix, parse_mode='HTML'
                            ),
                            reply_markup=markup_pix,
                        )
            except Exception as e:
                logging.error(f'Erro ao gerar pagamento: {e}')

        elif call.data.startswith('plan_'):
                try:
                    plan_mapping = {
                        'plan_1_month': (5, '1 mês', 30),
                        'plan_2_months': (10, '2 meses', 60),
                        'plan_3_months': (18, '3 meses', 90),
                    }

                    plan_key = call.data
                    if plan_key not in plan_mapping:
                        bot.answer_callback_query(call.id, 'Plano inválido.')
                        return

                    amount, plan_type, duration = plan_mapping[plan_key]

                    try:
                        # Criação de pagamento via PIX
                        payment_result = create_payment(amount, plan_type, duration)
                        if payment_result['status'] != 201:
                            error_message = payment_result.get('response', {}).get('message', 'Erro desconhecido')
                            bot.send_message(call.message.chat.id, f'Erro ao criar o pagamento: {error_message}')
                            return

                        # Extraindo informações do pagamento
                        payment_id = payment_result['response']['id']
                        pix_qr_code_base64 = payment_result['response']['point_of_interaction']['transaction_data']['qr_code_base64']
                        pix_copy_paste = payment_result['response']['point_of_interaction']['transaction_data']['qr_code']

                        # Decodificando a imagem do QR code
                        img_data = base64.b64decode(pix_qr_code_base64)
                        img = BytesIO(img_data)

                        # Enviando o QR code e o código copiar/colar
                        caption_pix_pg=f"Utilize o código abaixo para efetuar o pagamento:\n\n<code>{pix_copy_paste}</code>"
                        bot.edit_message_media(
                                            chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            media=types.InputMediaPhoto(
                                                media=img, caption=caption_pix_pg, parse_mode='HTML'
                                            ),
                                            reply_markup=markup,
                        )

                        # Armazena o payment_id e outras informações para verificação futura
                        pending_payments[str(payment_id)] = {
                            'user_id': call.from_user.id,
                            'timestamp': datetime.now(),
                            'plan_type': plan_type,
                            'duration': duration
                        }

                        # Envia botão para verificar pagamento
                        verify_keyboard = types.InlineKeyboardMarkup()
                        verify_keyboard.add(types.InlineKeyboardButton('✅ Verificar pagamento', callback_data=f'verify_payment|{payment_id}|{plan_type}|{duration}'))

                        bot.send_message(call.message.chat.id, "Após efetuar o pagamento, clique em 'Verificar pagamento' abaixo.", reply_markup=verify_keyboard)

                    except Exception as e:
                        bot.send_message(call.message.chat.id, f'Erro ao gerar pagamento: {e}')
                except Exception as e:
                    logging.error(f'Erro ao gerar pagamento: {e}')

        elif call.data.startswith('verify_payment'):
            try:
                callback_data_parts = call.data.split('|')
                if len(callback_data_parts) != 4:
                    bot.send_message(call.message.chat.id, 'Dados inválidos no callback. Por favor, tente novamente.')
                    return

                payment_id = callback_data_parts[1]
                plan_type = callback_data_parts[2]
                duration = int(callback_data_parts[3])

                try:
                    pix = TOKEN_MERCADOPAGO
                    payment_status = pix.check_payment_status(payment_id)

                    if payment_status['status'] == 'approved':
                        bot.send_message(call.message.chat.id, '✅ Pagamento confirmado! Sua assinatura será ativada em breve.')
                        user_id = call.from_user.id
                        current_datetime = datetime.now()
                        expiration_date = current_datetime + timedelta(days=duration)
                        initial_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

                        user_manager.update_user_info(user_id, 'premium', 'true')
                        user_manager.update_user_info(user_id, 'initial_date', initial_date)
                        user_manager.update_user_info(user_id, 'final_date', expiration_date.strftime('%Y-%m-%d %H:%M:%S'))

                        # Envia mensagem de sucesso com informações da assinatura
                        photo_paid = 'https://i.imgur.com/Vcwajly.png'
                        caption_sucess = (
                            f"🎉 <b>Pagamento bem-sucedido!</b>\n\n"
                            f"Você adquiriu <b>{plan_type}</b> para {duration} dias de acesso premium ao Curso Bot.\n"
                            "Agora você tem acesso ilimitado a todos os nossos cursos, com suporte prioritário.\n\n"
                            f"📅 <b>Seu acesso premium expira em:</b> {expiration_date.strftime('%d/%m/%Y')}\n\n"
                            "Aproveite sua jornada de aprendizado!"
                        )
                        markup = types.InlineKeyboardMarkup()
                        back_to_home = types.InlineKeyboardButton('↩️ Voltar', callback_data='menu_start')
                        markup.add(back_to_home)

                        bot.send_photo(
                            chat_id=call.message.chat.id,
                            photo=photo_paid,
                            caption=caption_sucess,
                            parse_mode='HTML',
                            reply_markup=markup,
                        )

                    else:
                        bot.send_message(call.message.chat.id, '❌ O pagamento ainda não foi aprovado. Tente novamente mais tarde.')

                except Exception as e:
                    bot.send_message(call.message.chat.id, f'Erro ao verificar pagamento: {e}')
            except Exception as e:
                logging.error(f'Erro ao gerar pagamento: {e}')

        elif call.data.startswith('estrela'):
            try:
                user_id = call.from_user.id
                user = user_manager.search_user(user_id)
                values_btn = types.InlineKeyboardMarkup()
                btn_50 = types.InlineKeyboardButton('⭐️ 50 Estrelas - 1 Mês', callback_data="50_estrelas")
                btn_100 = types.InlineKeyboardButton('⭐️ 100 Estrelas - 2 Meses', callback_data="100_estrelas")
                btn_150 = types.InlineKeyboardButton('⭐️ 200 Estrelas - 3 Meses', callback_data="200_estrelas")
                btn_termo = types.InlineKeyboardButton('📁 Termo de uso', url='https://telegra.ph/Termo-de-uso-09-28')
                btn_cancel = types.InlineKeyboardButton('Voltar', callback_data="comprar")

                values_btn.row(btn_50)
                values_btn.row(btn_100)
                values_btn.row(btn_150)
                values_btn.row(btn_termo)
                values_btn.row(btn_cancel)

                caption_nws = (
                        "⭐️ <b>Escolha seu plano de assinatura:</b>\n\n"
                        "Com a assinatura premium, você terá acesso ilimitado a todos os cursos, "
                        "suporte prioritário e a possibilidade de favoritar seus cursos preferidos. "
                        "Além disso, seu pagamento é feito de maneira anônima com estrelas do Telegram!\n\n"
                        "<blockquote>⭐️ 100 ≈ US$ 1,84</blockquote>"
                    )
                photo_pay = 'https://i.imgur.com/c3nzNhd.png'
                bot.edit_message_media(
                chat_id=call.from_user.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                        media=photo_pay, caption=caption_nws, parse_mode='HTML'
                    ),
                    reply_markup=values_btn,
                )
            except Exception as e:
                logging.error(f'Erro ao gerar pagamento: {e}')
        elif call.data in ["50_estrelas", "100_estrelas", "200_estrelas"]:
            try:
                user_id = call.from_user.id
                user = user_manager.search_user(user_id)
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id) 
                stars_map = {
                    "50_estrelas": 50,
                    "100_estrelas": 100,
                    "200_estrelas": 200
                }
                
                months_map = {
                    "50_estrelas": 1,
                    "100_estrelas": 2,
                    "200_estrelas": 3
                }
                
                selected_stars = stars_map[call.data]
                selected_months = months_map[call.data]
                description = (
                    f"Você está escolhendo a assinatura premium de {selected_months} mês(es)!" 
                    "\n\nLembre-se que você desbloquear "
                    "todos os recursos exclusivos do Curso Bot."
                )

                markup_stars = types.InlineKeyboardMarkup()
                back_to_pay_again = types.InlineKeyboardButton('↩️ Voltar', callback_data='pay_again')
                pay_button = types.InlineKeyboardButton(f'Pagar ⭐{selected_stars}', pay=True)

                markup_stars.add(pay_button)
                markup_stars.add(back_to_pay_again)

                bot.send_invoice(
                    call.from_user.id,
                    provider_token=None,  
                    title=f'Compra de {selected_stars} Estrelas - {selected_months} mês(es) de Premium',
                    description=description,
                    currency='XTR',  
                    prices=[
                        telebot.types.LabeledPrice(label=f'{selected_stars} Estrelas', amount=selected_stars )  
                    ],
                    start_parameter=f'stars_{selected_stars}',
                    invoice_payload=f'stars_{selected_stars}',
                    reply_markup=markup_stars
                )        
            except Exception as e:
                logging.error(f'Erro ao gerar pagamento: {e}')
        elif call.data.startswith('pay_again'):
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            user_id = call.from_user.id
            user = user_manager.search_user(user_id)
            is_premium = user.get('premium') == 'true'
            photo_pay = 'https://i.imgur.com/c3nzNhd.png'  
            
            photo_sub = 'https://i.imgur.com/bngnGuN.png'
            if is_premium:
                markup = types.InlineKeyboardMarkup()
                back_to_home = types.InlineKeyboardButton(
                '↩️ Voltar', callback_data='menu_start'
                )
                markup.add(back_to_home)

                final_date = datetime.strptime(user.get('final_date'), '%Y-%m-%d %H:%M:%S')
                days_left = (final_date - datetime.now()).days
        

                caption_sub = (
                    "<b>🎉 Parabéns! Você já é um assinante premium.</b>\n\n"
                    "💎 <b>Assinatura ativa:</b> Você tem acesso total aos cursos e funcionalidades do bot.\n"
                    f"📅 <b>Data de Expiração:</b> {user.get('final_date')}\n"
                    f"⏳ <b>Tempo restante:</b> {days_left} dias até a expiração da sua assinatura.\n\n"
                    "Caso deseje renovar ou alterar seu plano, basta escolher uma das opções abaixo."
                )
                bot.send_photo(
                    chat_id=call.from_user.id,
                    photo=photo_sub,  
                    caption=caption_sub,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            else:
                values_btn = types.InlineKeyboardMarkup()
                btn_50 = types.InlineKeyboardButton('⭐️ 50 Estrelas - 1 Mês', callback_data="50_estrelas")
                btn_100 = types.InlineKeyboardButton('⭐️ 100 Estrelas - 2 Meses', callback_data="100_estrelas")
                btn_150 = types.InlineKeyboardButton('⭐️ 200 Estrelas - 3 Meses', callback_data="200_estrelas")
                btn_cancel = types.InlineKeyboardButton('Cancelar', callback_data="menu_start")
                values_btn.row(btn_50)
                values_btn.row(btn_100)
                values_btn.row(btn_150)
                values_btn.row(btn_cancel)

                caption_nws = (
                    "⭐️ <b>Escolha seu plano de assinatura:</b>\n\n"
                    "Com a assinatura premium, você terá acesso ilimitado a todos os cursos, "
                    "suporte prioritário e a possibilidade de favoritar seus cursos preferidos. "
                    "Além disso, seu pagamento é feito de maneira anônima com estrelas do Telegram!\n\n"
                    "<blockquote>⭐️ 100 ≈ US$ 1,84</blockquote>"
                )
                bot.send_photo(
                    chat_id=call.from_user.id,
                    photo=photo_pay,  
                    caption=caption_nws,
                    parse_mode='HTML',
                    reply_markup=values_btn
                )
        elif call.data.startswith('categoria'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            top1 = types.InlineKeyboardButton("📅 Ano de lançamento", switch_inline_query_current_chat="ano=2021")
            top2 = types.InlineKeyboardButton("🎭 Categoria", switch_inline_query_current_chat="genero=Python")
            top3 = types.InlineKeyboardButton("📝 Primeira letra do curso", switch_inline_query_current_chat="letra=c")
            top4 = types.InlineKeyboardButton("💾 Histórico", switch_inline_query_current_chat="HISTORICO")
            top5 = types.InlineKeyboardButton("❤️ Favorito", switch_inline_query_current_chat="FAVORITO")
            back_button = telebot.types.InlineKeyboardButton(text="↩️ Voltar", callback_data="menu_start")
            markup.add(top5)
            markup.add(top1, top2)
            markup.add(top3, top4)
            markup.add(back_button)

            message_text = f'<b>Filtros de busca</b>\n\nSelecione uma das opções de filtro abaixo:\n\n- <b>Favorito:</b> Tenha seus cursos favoritos de forma simples e rápida. (Pode usar como uma lista de cursos que você quer ver no futuro).\n- <b>Ano de lançamento (busca o ano)</b>: Encontre cursos lançados em um ano específico\n- <b>Categoria (busca pelo tipo de Categoria)</b>: Procure cursos pela Categoria, como programacao, portugues, ingles, etc.\n- <b>Primeira letra</b>: Descubra os cursos pela primeira letra.\n- <b>Histórico:</b> Tenha o histórico de último vídeo do curso visto, para facilitar seu acesso.'
            photo_url = 'https://i.imgur.com/ArmCfsW.png'

            categoria_media = telebot.types.InputMediaPhoto(media=photo_url, caption=message_text, parse_mode="HTML")
            bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=categoria_media, reply_markup=markup)
        elif call.data.startswith('config'):
            user_id = call.from_user.id
            user_data = user_manager.search_user(user_id)
            if user_data:
                message_text = f"<b><u>Configurações do Usuário:</u></b>\n\n"
                message_text += f"<b>•Name:</b> {user_data['first_name']}\n"
                message_text += f"<b>•ID:</b> {user_data['user_id']}\n"
                message_text += f"<b>•Assinatura:</b> {'Ativada' if user_data['premium'] == 'true' else 'Desativada'}\n"
                if user_data['premium'] == 'true':
                    final_date = user_data['final_date']
                    message_text += f"<b>•Data de Expiração:</b> {final_date}\n"
                indicacao = user_data['indicacao'] if user_data['indicacao'] else "0"
                message_text += f"<b>•Indicações:</b> {indicacao}\n\n"
                message_text += f"🔗 Link: <code>https://t.me/CursoBRBot?start={user_id}</code>"

                reply_markup = telebot.types.InlineKeyboardMarkup()
                back_button = telebot.types.InlineKeyboardButton(text="↩️ Voltar", callback_data="menu_start")
                reply_markup.row(back_button)

                photo_url = 'https://i.imgur.com/2R9HlZY.png'
                photo = telebot.types.InputMediaPhoto(media=photo_url, caption=message_text, parse_mode="HTML")

                bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=photo, reply_markup=reply_markup)
            else:
                logging.debug(user_id, "Usuário não encontrado no banco de dados.")
        elif call.data.startswith('indique'):
            user_id = call.from_user.id
            user_id = call.from_user.id  
            message_text_report = f"<b>Interessado em apoiar nosso projeto, beneficiar seus amigos e ainda ser recompensado por isso? Se a resposta for sim, o processo é bastante direto.</b>\n\nAo convidar alguém para utilizar nosso bot através do seu link de referência e essa pessoa efetuar uma contribuição, você receberá dias de contribuição gratuitos. Não importa o montante ou a frequência das contribuições, o benefício será sempre seu.\n<i>➥ Observação: o seu amigo não pode ter previamente utilizado nossos bots.</i>\n\nSeu link: <code>https://t.me/CursoBRBot?start={user_id}</code>\n\n💡Clique no link para copia-lo."
            photo_url = 'https://i.imgur.com/accz8YZ.png'

            reply_markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton(text="↩️ Voltar", callback_data="menu_start")
            reply_markup.row(back_button)

            indique_media = telebot.types.InputMediaPhoto(media=photo_url, caption=message_text_report, parse_mode="HTML")
            bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=indique_media, reply_markup=reply_markup)
        elif call.data.startswith('commands'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            back_to_home = types.InlineKeyboardButton(
                '↩️ Voltar', callback_data='menu_help'
            )
            markup.add(back_to_home)
            msg_text = (
                '<b>Lista de comandos</b>\n\n'
                '/start - Início do bot 🙂\n'
                '/help - Ajuda do bot\n'
                '/add_fav - Adicionando categoria favorita\n'
                '/rem_fav - Removendo categoria favorita\n'
                '/my_fav - Sua categoria favorita'
            )
            photo = 'https://i.imgur.com/eLNCvoF.png'
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo, caption=msg_text, parse_mode='HTML'
                ),
                reply_markup=markup,
            )
        elif call.data.startswith('more'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            assinatura = types.InlineKeyboardButton(
                text='🎫 Assinatura', callback_data='comprar'
            )
            pres_btn = types.InlineKeyboardButton(
                '➡️ Próximo', callback_data='press_text_two'
            )
            back_to_home =  types.InlineKeyboardButton(
                '⬅️ Retornar', callback_data='menu_start'
            )   
            markup.add(back_to_home, pres_btn)
            markup.add(assinatura)
            photo_url = 'https://i.imgur.com/n6fFGYg.jpeg'

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo_url, caption=msg_text_1, parse_mode='HTML'
                ),
                reply_markup=markup,
            )

        elif call.data.startswith('press_text_two'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            back_to_home = types.InlineKeyboardButton(
                '#️⃣ Início', callback_data='menu_start'
            )   
            assinatura = types.InlineKeyboardButton(
                text='🎫 Assinatura', callback_data='comprar'
            )
            pres_btn = types.InlineKeyboardButton(
                '➡️ Próximo', callback_data='press_text_three'
            )
            back_to_press =  types.InlineKeyboardButton(
                '⬅️ Retornar', callback_data='more'
            )   
            markup.add(back_to_home)
            markup.add(back_to_press, pres_btn)
            markup.add(assinatura)
            photo_url = 'https://i.imgur.com/n6fFGYg.jpeg'

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo_url, caption=msg_text_2, parse_mode='HTML'
                ),
                reply_markup=markup,
            )

        elif call.data.startswith('press_text_three'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            back_to_home = types.InlineKeyboardButton(
                '#️⃣ Início', callback_data='menu_start'
            )   
            assinatura = types.InlineKeyboardButton(
                text='🎫 Assinatura', callback_data='comprar'
            )
            back_to_press_two =  types.InlineKeyboardButton(
                '⬅️ Retornar', callback_data='press_text_two'
            )   
            markup.add(back_to_press_two, back_to_home)
            markup.add(assinatura)
            photo_url = 'https://i.imgur.com/n6fFGYg.jpeg'

            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo_url, caption=msg_text_3, parse_mode='HTML'
                ),
                reply_markup=markup,
            )
        elif call.data.startswith('doacao'):
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            back_to_home = types.InlineKeyboardButton(
                '↩️ Voltar', callback_data='menu_start'
            )
            markup.add(back_to_home)
            text_msg = (
                '──❑ D 「 🤝 Doação 」❑──\n\n'
                ' ☆ <b>Pix:</b>\n <code>32dc79d2-2868-4ef0-a277-2c10725341d4</code>\n\n'
                ' ☆ <b>BTC:</b>\n <code>bc1qjxzlug0cwnfjrhacy9kkpdzxfj0mcxc079axtl</code>\n\n'
                ' ☆ <b>ETH/USDT:</b>\n <code>0x1fbde0d2a96869299049f4f6f78fbd789d167d1b</code>'
            )

            photo = 'https://i.imgur.com/n6nWmM9.png'
            bot.edit_message_media(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                media=types.InputMediaPhoto(
                    media=photo, caption=text_msg, parse_mode='HTML'
                ),
                reply_markup=markup,
            )
        elif call.data.startswith('set_category'):
            set_favorite_category(call)
        elif call.data.startswith('REMOVE_VOTE '):
            remove_vote_callback(call)
        elif call.data.startswith('ADD_LIKE '):
            add_like_callback_handler(call)
        elif call.data.startswith('ADD_DESLIKE '):
            add_deslike_callback_handler(call)
        elif call.data.startswith('ADD_MY_FAV '):
            add_to_my_fav_list(call)
        elif call.data.startswith('REMOVE_MY_FAV '):
            remove_from_my_fav_list(call)
        elif call.data.startswith('previous_media'):
            previous_media_callback(call)
        elif call.data.startswith('next_media'):
            next_media_callback(call)
        elif call.data.startswith('voltar_info'):
            menu_curso_callback(call)
    except Exception as e:
        logging.error(f'Erro ao callback_handler: {e}')

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    try: 
        payload = message.successful_payment.invoice_payload
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        
        if not user:
            logging.error("Erro: usuário não encontrado no banco de dados.")
            user_manager.add_user_db(message)
            user = user_manager.search_user(user_id)
            user_info = f"<b>#{bot.get_me().username} #New_User</b>\n<b>User:</b> {user['first_name']}\n<b>ID:</b> <code>{user['user_id']}</code>\n<b>Username</b>: @{user.get('username', 'Sem Username')}"
            bot.send_message(GROUP_LOG_ID, user_info, message_thread_id=43147)


        if payload == 'stars_50':
            months = 1
            payload_text = '50 estrela'
        elif payload == 'stars_100':
            months = 2
            payload_text = '100 estrelas'
        elif payload == 'stars_200':
            months = 3
            payload_text = '200 estrelas'
        else:
            logging.error("Erro: o valor do pagamento não é válido.")
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
                    initial_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                    new_date_obj = datetime.now() + timedelta(days=1)
                    final_date = new_date_obj.strftime('%Y-%m-%d %H:%M:%S')  
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
            f"<b>Valor:</b> {payload_text}\n"
            f"<b>Período:</b> {months} mês(es)"
        )
        bot.send_message(PAYMENT_POST_ID, user_info)
    except Exception as e:
        logging.error(f'Erro ao efetuar o pagamento: {e}')

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=True,
            error_message='Erro. Tente novamente mais tarde.'
        )
    except Exception as e:
        logging.error(f'Erro ao checar o pagamento: {e}')



def verificar_assinaturas():
    try:
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        users = user_manager.get_all_users()
        logging.info("Iniciando verificação de assinaturas...")

        for user in users:
            final_date_str = user.get('final_date')
            user_id = user.get('user_id')

            if final_date_str:
                try:
                    final_datetime = datetime.strptime(final_date_str, '%Y-%m-%d %H:%M:%S')
                    final_date = final_datetime.date()
                except ValueError:
                    logging.error(f"Formato de data inválido para o usuário {user_id}: {final_date_str}")
                    continue

                notify_date = final_date - timedelta(days=1)

                # Notificar 1 dia antes
                if notify_date == current_date:
                    try:
                        bot.send_message(
                            user_id,
                            "Sua assinatura está expirando em 24 horas. Por favor, renove amanhã para continuar utilizando nossos serviços."
                        )
                        logging.info(f"Notificação enviada para o usuário {user_id} sobre expiração em 24 horas.")
                    except Exception as e:
                        logging.error(f"Erro ao enviar notificação para o usuário {user_id}: {e}")

                # Verificar se a assinatura expirou
                elif final_date <= current_date:
                    try:
                        user_manager.update_user_info(user_id, 'premium', 'false')
                        user_manager.update_user_info(user_id, 'initial_date', '')
                        user_manager.update_user_info(user_id, 'final_date', '')
                        bot.send_message(
                            user_id,
                            "Sua assinatura expirou. Renove-a no botão Assinaturas ou /renovar_assinatura para continuar tendo acesso ao sistema e não perder os novos lançamentos."
                        )
                        logging.info(f"Assinatura expirou para o usuário {user_id}. Informações atualizadas.")
                    except Exception as e:
                        logging.error(f"Erro ao atualizar assinatura para o usuário {user_id}: {e}")
                else:
                    logging.debug(f"Usuário {user_id} não precisa de ação hoje.")
            else:
                logging.debug(f"Usuário {user_id} não possui 'final_date'.")
    except Exception as e:
        logging.error(f'Erro ao verificar assinaturas: {e}')


@bot.message_handler(commands=['add_fav'])
def choose_favorite_category(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        if message.chat.type == 'private':
            categories = video_manager.db.videos.distinct("categoria")

            if not categories:
                bot.send_message(message.chat.id, "Nenhuma categoria disponível no momento.")
                return
            
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(category, callback_data=f"set_category:{category}") for category in categories]
            for i in range(0, len(buttons), 3):
                markup.row(*buttons[i:i+3])

            bot.send_message(message.chat.id, "<b>Escolha sua categoria favorita:</b>\n\nLembrando isso servirá para você receber recomendações toda a sexta do curso com essa categoria. Para remover digite /del_fav", reply_markup=markup)
    except Exception as e:
        logging.error(f'Erro ao adicionar favorito: {e}')

def set_favorite_category(call):
    try:
        user_id = call.from_user.id
        category = call.data.split(":")[1]

        users_collection = user_manager.db.users
        users_collection.update_one({'user_id': user_id}, {'$set': {'favorite': category}})

        confirmation_msg = f"Sua categoria foi definida como {category}"

        bot.edit_message_text(
            text=confirmation_msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
                )
    except Exception as e:
        logging.error(f'Erro ao adicionar favorito: {e}')



@bot.message_handler(commands=['del_fav'])
def delete_favorite_category(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        if message.chat.type == 'private':
            user_id = message.from_user.id

            users_collection = user_manager.db.users
            users_collection.update_one({'user_id': user_id}, {'$set': {'favorite': ''}})

            confirmation_msg = "<b>Sua categoria favorita foi removida!</b>\n\nA partir de agora, você não receberá mais recomendações nas sextas-feiras. Para adicionar de novo digite /add_fav"

            bot.send_message(message.chat.id, confirmation_msg)
    except Exception as e:
        logging.error(f'Erro ao remover favorito: {e}')

@bot.message_handler(commands=['my_fav'])
def my_favorite_category(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        if message.chat.type == 'private':
            user_id = message.from_user.id

            users_collection = user_manager.db.users
            user_data = users_collection.find_one({'user_id': user_id})

            if user_data and 'favorite' in user_data and user_data['favorite']:
                fav = user_data['favorite']
                my_fav_msg = f"<b>Sua categoria favorita é: {fav}</b>"
            else:
                my_fav_msg = (
                    "<b>Você ainda não tem uma categoria favorita definida.</b>\n\n"
                    "Use o comando /add_fav para escolher sua categoria favorita."
                )

            bot.send_message(message.chat.id, my_fav_msg, parse_mode="HTML")
    except Exception as e:
        logging.error(f'Erro ao remover favorito: {e}')

curso_queue_fav = []

def send_recommendations():
    try:
        users_collection = user_manager.db.users
        users_with_favorite = users_collection.find({'favorite': {'$ne': ''}})

        for user in users_with_favorite:
            favorite_category = user['favorite']
            curso_with_category = list(video_manager.db.videos.find({'categoria': favorite_category}))

            if curso_with_category:
                selected_curso = random.choice(curso_with_category)
                
                caption = (
                    f"<b>Sextôuu! Que tal maratona essa?</b>\n\n"
                    f"<b>Nome:</b> {selected_curso.get('nome')}\n"
                    f"<b>Lançamento:</b> {selected_curso.get('lanc')}\n"
                    f"<b>Duração:</b> {selected_curso.get('duracao')}\n"
                    f"<b>Categoria:</b> {selected_curso.get('categoria')}\n\n"
                    f"<b>Tamanho:</b> {selected_curso.get('tamanho')}\n\n"
                    f"<b>Criador:</b> {selected_curso.get('criado')}\n\n"
                    f"<b>Descrição:</b> {selected_curso.get('description')}"
                    f"Para parar de receber essa mensagem digite /del_fav"
                )
                
                inline_button = types.InlineKeyboardButton(
                    text="▶️ Assistir",
                    switch_inline_query_current_chat=selected_curso.get('nome')
                )
                
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(inline_button)

                try:
                    bot.send_photo(user['user_id'], selected_curso.get('thumb_nail'), caption=caption, reply_markup=keyboard, parse_mode="HTML")
                    logging.info(f"Recomendação enviada para o usuário {user['user_id']}")
                except Exception as send_error:
                    logging.error(f"Erro ao enviar recomendação para o usuário {user['user_id']}: {send_error}")
                
                time.sleep(2)
            else:
                logging.debug(f"Nenhum curso encontrado na categoria {favorite_category} para o usuário {user['user_id']}")
                
    except Exception as e:
        logging.error(f"Erro geral no envio de recomendações: {e}")


class CursoSearcher:
    def __init__(self, video_manager):
        self.video_manager = video_manager

    def search_by_partial_name(self, partial_name: str) -> List[Dict]:
        regex_pattern = re.escape(partial_name)
        regex_pattern = regex_pattern.replace(r"\'", r"\'?")
        regex_pattern = f".*{regex_pattern}.*"
        return list(self.video_manager.db.videos.find({
            "nome": {"$regex": regex_pattern, "$options": "i"}
        }))

    def search_by_name_and_season(self, identificador: str, temporada: int) -> List[Dict]:
        return list(self.video_manager.db.videos.find({
            "idnt": identificador,
            "temp": temporada
        }))


    def search_by_year(self, ano: int) -> List[Dict]:
        return list(self.video_manager.db.videos.find({
            "lanc": ano,
            "nome": {"$ne": ""}
        }))

    def search_by_categoria(self, categoria: str) -> List[Dict]:
        return list(self.video_manager.db.videos.find({
            "categoria": str(categoria),
        }))

    def search_by_first_letter(self, first_letter: str) -> List[Dict]:
        regex_pattern = f"^{re.escape(first_letter)}"
        return list(self.video_manager.db.videos.find({
            "nome": {"$regex": regex_pattern, "$options": "i"}
        }))

    def search_by_temp_total(self, temp_total: int) -> List[Dict]:
        return list(self.video_manager.db.videos.find({
            "temp_total": int(temp_total),
            "nome": {"$ne": ""},
        }))

def create_inline_results(cursos: List[Dict]) -> List[types.InlineQueryResultArticle]:
    results = []
    for index, curso in enumerate(cursos[:25]):
        title = curso.get("nome", "Curso sem nome")
        result_id = f"curso_{curso.get('id', index)}_{index}"
        idnt = curso.get("idnt", "")
        thumbnail_url = curso.get("thumb_nail", "")
        assistir = f"ASSISTIR={idnt}"

        description = (
            f"{curso.get('lanc', 'Sem data')} - "
            f"{curso.get('categoria', '')}\n"
            f"Veja o curso {title}"
        )

        result = types.InlineQueryResultArticle(
            id=result_id,
            thumbnail_url=thumbnail_url,
            description=description,
            title=title,
            input_message_content=types.InputTextMessageContent(
                message_text=assistir,
            ),
        )
        results.append(result)
    return results

@bot.inline_handler(lambda query: True)
def inline_query(query):
    try:
        query_text = query.query.strip()
        
        if not query_text:
            # Handle empty query
            handle_empty_query(query)
            return

        user_id = query.from_user.id
        user = user_manager.search_user(user_id)

        if not user:
            user = user_manager.add_user_db(query.from_user)

        searcher = CursoSearcher(video_manager)

        # Define command handlers
        command_handlers = {
            'ano=': handle_ano_query,
            'genero=': handle_genero_query,
            'letra=': handle_letra_query,
            'EPISODIO=': handle_episodio_query,
            'HISTORICO': handle_historico_query,
            'FAVORITO': handle_favorito_query,
        }

        # Check if query_text matches any command prefix
        for prefix, handler in command_handlers.items():
            if query_text.startswith(prefix):
                handler(query, query_text, searcher, user)
                return

        # Default handler (search by partial name)
        handle_default_query(query, query_text, searcher)

    except Exception as e:
        logging.error(f"Erro na consulta inline: {e}")
        bot.answer_inline_query(query.id, [], cache_time=0)

def handle_empty_query(query):
    result_inicial = types.InlineQueryResultArticle(
        id="inicial",
        title="Digite o nome do curso",
        description="Para encontrar, digite corretamente o nome do curso",
        input_message_content=types.InputTextMessageContent(
            message_text="Exemplo: @cursobrbot Python"
        ),
        thumbnail_url="https://i.imgur.com/oCjERKj.png",
    )
    bot.answer_inline_query(
        query.id,
        [result_inicial],
        switch_pm_text='Como usar o bot?',
        switch_pm_parameter='how_to_use',
        cache_time=0
    )

def handle_ano_query(query, query_text, searcher, user):
    match = re.match(r"ano=(\d{4})", query_text)
    if match:
        ano = int(match.group(1))
        cursos = searcher.search_by_year(ano)
        results = create_inline_results(cursos)
        if results:
            bot.answer_inline_query(query.id, results)
        else:
            send_no_results(query)
    else:
        send_invalid_command(query)

def handle_genero_query(query, query_text, searcher, user):
    match = re.match(r"genero=(\w+)", query_text)
    if match:
        categoria = str(match.group(1))
        cursos = searcher.search_by_categoria(categoria)
        results = create_inline_results(cursos)
        if results:
            bot.answer_inline_query(query.id, results)
        else:
            send_no_results(query)
    else:
        send_invalid_command(query)

def handle_letra_query(query, query_text, searcher, user):
    match = re.match(r"letra=(\w)", query_text)
    if match:
        letra = match.group(1)
        cursos = searcher.search_by_first_letter(letra)
        results = create_inline_results(cursos)
        if results:
            bot.answer_inline_query(query.id, results)
        else:
            send_no_results(query)
    else:
        send_invalid_command(query)

def handle_episodio_query(query, query_text, searcher, user):
    match = re.match(r"EPISODIO=\s*(.+)\s+(\d+)", query_text)
    if match:
        identificador = match.group(1).strip()
        temporada = int(match.group(2))
        curso_open = searcher.search_by_name_and_season(identificador, temporada)

        if not curso_open:
            send_course_not_found(query)
            return

        # Implementação da paginação
        try:
            offset = int(query.offset) if query.offset else 0
        except ValueError:
            offset = 0

        limit = 25
        next_offset = offset + limit

        # Obter os resultados de acordo com o offset e o limite
        paginated_cursos = curso_open[offset:offset+limit]

        results = []
        for index, curso_opens in enumerate(paginated_cursos, start=offset):
            title = curso_opens.get("description")
            result_id = f"curso_open_{curso_opens.get('id')}_{index}"
            episodio = curso_opens.get("episodio")
            idnt = curso_opens.get("idnt")
            temp = curso_opens.get("temp")
            thumbnail_url = curso_opens.get("thumb_nail")
            assistir = f"EPISODIO={idnt} {temp} {episodio}"
            description = (
                f"Temporada: {temp}\n"
                f"Episódio: {episodio}"
            )

            article_result = types.InlineQueryResultArticle(
                id=result_id,
                thumbnail_url=thumbnail_url,
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(
                    message_text=assistir,
                ),
            )
            results.append(article_result)

        # Verifica se há mais resultados para fornecer o next_offset
        if len(curso_open) > next_offset:
            bot.answer_inline_query(query.id, results, next_offset=str(next_offset))
        else:
            bot.answer_inline_query(query.id, results, next_offset='')

    else:
        send_invalid_command(query)



def handle_historico_query(query, query_text, searcher, user):
    historico = user.get('historico', '')
    
    if historico:
        historico_parts = historico.split(' ')
        if len(historico_parts) == 3:
            identificador = historico_parts[0]
            temporada = int(historico_parts[1])
            episodio = int(historico_parts[2])

            curso = video_manager.db.videos.find_one({
                "idnt": identificador,
                "temp": temporada,
                "episodio": episodio
            })

            if not curso:
                send_episode_not_found(query)
                return

            title = curso.get("description")
            result_id = f"curso_{curso.get('id')}"
            thumbnail_url = curso.get("thumb_nail")
            assistir = f"EPISODIO={identificador} {temporada} {episodio}"
            description = (
                f"Temporada: {temporada}\n"
                f"Episódio: {episodio}"
            )

            article_result = types.InlineQueryResultArticle(
                id=result_id,
                thumbnail_url=thumbnail_url,
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(
                    message_text=assistir,
                ),
            )
            results = [article_result]
            bot.answer_inline_query(query.id, results)
        else:
            send_invalid_historico(query)
    else:
        send_empty_historico(query)

def handle_favorito_query(query, query_text, searcher, user):
    favoritos = user.get('my_fav', [])
    
    if favoritos:
        results = []
        for index, identificador in enumerate(favoritos[:25]):
            identificador = identificador.strip()
            if identificador:
                curso = video_manager.db.videos.find_one({
                    "idnt": identificador,
                })

                if not curso:
                    error_result = types.InlineQueryResultArticle(
                        id=f"curso_nao_encontrado_{index}",
                        title="Curso não encontrado",
                        description="Clique aqui para saber o motivo",
                        input_message_content=types.InputTextMessageContent(
                            message_text="Por favor, tente novamente... Se o erro persistir, entre em contato com o suporte"
                        ),
                        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
                    )
                    results.append(error_result)
                    continue

                title = curso.get("description")
                episodio = curso.get("episodio")
                temporada = curso.get("temp")
                result_id = f"curso_{curso.get('id')}"
                thumbnail_url = curso.get("thumb_nail")
                assistir = f"ASSISTIR={identificador}"
                description = (
                    f"Temporada: {temporada}\n"
                    f"Episódio: {episodio}"
                )

                article_result = types.InlineQueryResultArticle(
                    id=result_id,
                    thumbnail_url=thumbnail_url,
                    title=title,
                    description=description,
                    input_message_content=types.InputTextMessageContent(
                        message_text=assistir,
                    ),
                )
                results.append(article_result)
            else:
                continue  # Skip empty identifiers

        if results:
            bot.answer_inline_query(query.id, results)
        else:
            send_empty_favoritos(query)
    else:
        send_empty_favoritos(query)

def handle_default_query(query, query_text, searcher):
    cursos = searcher.search_by_partial_name(query_text)
    results = create_inline_results(cursos)
    if results:
        bot.answer_inline_query(query.id, results)
    else:
        send_no_results(query)

def send_no_results(query):
    result_default = types.InlineQueryResultArticle(
        id="nenhum",
        title="Nenhum resultado encontrado",
        description="Tente outro termo de busca",
        input_message_content=types.InputTextMessageContent(
            message_text="Nenhum curso encontrado para a sua busca."
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [result_default], cache_time=0)

def send_invalid_command(query):
    error_result = types.InlineQueryResultArticle(
        id="comando_invalido",
        title="Comando inválido",
        description="Verifique o comando e tente novamente",
        input_message_content=types.InputTextMessageContent(
            message_text="Comando inválido. Por favor, tente novamente."
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [error_result], cache_time=0)

def send_course_not_found(query):
    error_result = types.InlineQueryResultArticle(
        id="curso_nao_encontrado",
        title="Curso não encontrado",
        description="Clique aqui para saber o motivo",
        input_message_content=types.InputTextMessageContent(
            message_text="Por favor, tente novamente... Se o erro persistir, entre em contato com o suporte"
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [error_result])

def send_episode_not_found(query):
    error_result = types.InlineQueryResultArticle(
        id="episodio_nao_encontrado",
        title="Episódio não encontrado",
        description="Clique aqui para saber o motivo",
        input_message_content=types.InputTextMessageContent(
            message_text="Por favor, tente novamente... Se o erro persistir, entre em contato com o suporte"
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [error_result])

def send_invalid_historico(query):
    error_result = types.InlineQueryResultArticle(
        id="historico_invalido",
        title="Histórico inválido",
        description="Não foi possível interpretar o seu histórico",
        input_message_content=types.InputTextMessageContent(
            message_text="Histórico inválido. Por favor, tente novamente."
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [error_result])

def send_empty_historico(query):
    result_default = types.InlineQueryResultArticle(
        id="nenhum_historico",
        title="Histórico vazio",
        description="Você ainda não assistiu a nenhum episódio.",
        input_message_content=types.InputTextMessageContent(
            message_text="Seu histórico está vazio."
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [result_default], cache_time=0)

def send_empty_favoritos(query):
    result_default = types.InlineQueryResultArticle(
        id="nenhum_favorito",
        title="Você não possui cursos favoritados",
        description="Você ainda não favoritou nenhum episódio.",
        input_message_content=types.InputTextMessageContent(
            message_text="Seu favorito está vazio. Escolha algum curso e clique em adicionar aos favoritos"
        ),
        thumbnail_url="https://i.imgur.com/UjaiwTf.png",
    )
    bot.answer_inline_query(query.id, [result_default], cache_time=0)

@bot.message_handler(func=lambda message: message.text.startswith("ASSISTIR="))
def handle_assistir_command(message):
    try:
        text = message.text

        parts = text.split("=")
        if len(parts) == 2:
            idnt = parts[1]
            send_curso_details(message, idnt)
        else:
            bot.answer_callback_query(message, text="Formato incorreto. Use 'ASSISTIR={idnt}' para buscar um curso.", show_alert=True)
    except Exception as e:
        logging.error(f"Ocorreu um erro ao capturar o ASSISTIR=: {e}")

def search_curso_by_id(idnt):
    result = video_manager.db.videos.find_one({"idnt": str(idnt), "nome": {"$ne": ""}})
    return result

def get_temp_total(idnt):
    """
    Retorna o número total de temporadas para um determinado idnt.
    
    :param idnt: O identificador do curso.
    :return: Número total de temporadas (int).
    """
    # Obtém os valores distintos de 'temp' para o idnt fornecido
    temps = video_manager.db.videos.find({'idnt': idnt}).distinct('temp')
    return len(temps)

def increment_curso_view(idnt):
    """
    Incrementa o contador de visualizações de um curso no banco de dados.

    Args:
        idnt (str): Identificador único do curso.
    """
    try:
        curso = search_curso_by_id(idnt)
        if curso:
            current_views = int(curso.get('view', 0))
            new_views = current_views + 1
            video_manager.update_curso(idnt, {'view': new_views})
        else:
            pass
    except Exception as e:
        logging.error(f"Erro ao incrementar visualizações para o curso {idnt}: {e}")


def send_curso_details(message, idnt):
    try:
        bot.send_chat_action(message.chat.id, 'upload_photo')
        idnt = str(idnt)
        curso = search_curso_by_id(idnt)
        user_id = message.from_user.id
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        if curso:   
            temp = int(curso.get('temp', 0))
            if temp is None:
                temp = 0 

            total_likes = int(curso.get('like', 0))
            total_dislikes = int(curso.get('deslike', 0))
            views = int(curso.get('view', 0))

            caption = (
                f"<b>Nome:</b> {curso.get('nome')}\n"
                f"<b>Lançamento:</b> {curso.get('lanc')}\n"
                f"<b>Duração:</b> {curso.get('duracao')}\n"
                f"<b>Categoria:</b> {curso.get('categoria')}\n"
                f"<b>Tamanho:</b> {curso.get('tamanho')}\n"
                f"<b>Criador:</b> {curso.get('criado')}\n\n"
            )

            photo = curso.get('thumb_nail')
            identificador = curso.get('idnt')
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            user_data = user_manager.search_user(user_id)
            my_fav_list = user_data.get('my_fav', [])
            is_in_my_fav = identificador in my_fav_list

            if is_in_my_fav:
                my_fav_button = types.InlineKeyboardButton(
                    "➖ Remover da Minha Lista", 
                    callback_data=f"REMOVE_MY_FAV {identificador}"
                )
            else:
                my_fav_button = types.InlineKeyboardButton(
                    "➕ Adicionar à Minha Lista", 
                    callback_data=f"ADD_MY_FAV {identificador}"
                )
            keyboard.add(my_fav_button)

            vote = vote_manager.search_vote(user_id, identificador)

            if vote:
                mode = vote.get('mode')
                remove_vote_button = types.InlineKeyboardButton(
                    "🗑 Remover Voto", 
                    callback_data=f"REMOVE_VOTE {identificador} {mode}"
                )
                keyboard.add(remove_vote_button)
            else:
                like_button = types.InlineKeyboardButton(
                    "👍 Like", 
                    callback_data=f"ADD_LIKE {identificador}"
                )
                deslike_button = types.InlineKeyboardButton(
                    "👎 Deslike", 
                    callback_data=f"ADD_DESLIKE {identificador}"
                )
                keyboard.add(like_button, deslike_button)
            
            temp_total = get_temp_total(idnt)

            for temp in range(1, temp_total + 1):
                text = f"▶️ Temporada {temp}"
                callback_data = f"EPISODIO= {identificador} {temp}"
                button = types.InlineKeyboardButton(text, switch_inline_query_current_chat=callback_data)
                keyboard.add(button)

            like_percentage = 0
            if total_likes + total_dislikes > 0:
                like_percentage = int((total_likes / (total_likes + total_dislikes)) * 100)

            star_rating = '⭐️'  
            if like_percentage >= 20 and like_percentage < 40:
                star_rating = '⭐️⭐️'
            elif like_percentage >= 40 and like_percentage < 60:
                star_rating = '⭐️⭐️⭐️'
            elif like_percentage >= 60 and like_percentage < 80:
                star_rating = '⭐️⭐️⭐️⭐️'
            elif like_percentage >= 80:
                star_rating = '⭐️⭐️⭐️⭐️⭐️'

            caption += (
                f"\n\n<b>Recomendação:</b> {star_rating}\n"
                f"<b>Visualizações:</b> {views}"
            )

            bot.send_photo(chat_id=message.chat.id, photo=photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            increment_curso_view(idnt)
        else:
            bot.answer_callback_query(message.chat.id, text="Formato incorreto. Use 'ASSISTIR={idnt}' para buscar um curso.", show_alert=True)
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")

def update_curso_deslike_count(identificador):
    try:
        serie_data = video_manager.search_videos_idnt(identificador)
        if serie_data and 'nome' in serie_data and serie_data['nome']:
            if 'deslike' in serie_data:
                serie_data['deslike'] = max(0, serie_data['deslike'] + 1)
            video_manager.db.videos.update_many({'idnt': identificador, 'nome': {'$ne': ''}}, {'$set': {'deslike': serie_data['deslike']}})
    except Exception as e:
        logging.error(f"Ocorreu um erro ao atualizado o contador de deslike +: {e}")


def update_curso_deslike_count_menos(identificador, remove=False):
    try:
        serie_data = video_manager.search_videos_idnt(identificador)
        if serie_data and 'deslike' in serie_data:
            if serie_data['deslike'] >= 1:
                serie_data['deslike'] = max(0, serie_data['deslike'] - 1)
            video_manager.db.videos.update_many({'idnt': identificador}, {'$set': {'deslike': serie_data['deslike']}})
    except Exception as e:
        logging.error(f"Ocorreu um erro ao atualizado o contador de deslike -: {e}")

def update_curso_like_count_menos(identificador, remove=False):
    try:
        serie_data = video_manager.search_videos_idnt(identificador)
        if serie_data and 'like' in serie_data:
            if serie_data['like'] >= 1:
                serie_data['like'] = max(0, serie_data['like'] - 1)
            video_manager.db.videos.update_many({'idnt': identificador}, {'$set': {'like': serie_data['like']}})
    except Exception as e:
        logging.error(f"Ocorreu um erro ao atualizado o contador de like -: {e}")

def update_curso_like_count(identificador):
    try:
        serie_data = video_manager.search_videos_idnt(identificador)
        if serie_data and 'nome' in serie_data and serie_data['nome']:
            if 'like' in serie_data:
                serie_data['like'] = max(0, serie_data['like'] + 1)
            video_manager.db.videos.update_many({'idnt': identificador, 'nome': {'$ne': ''}}, {'$set': {'like': serie_data['like']}})
    except Exception as e:
        logging.error(f"Ocorreu um erro ao atualizado o contador de like +: {e}")


def remove_vote_callback(call):
    try: 
        user_id = call.from_user.id
        callback_data = call.data.split()

        if len(callback_data) >= 3:
            identificador = callback_data[1]
            mode = callback_data[2]

            vote = vote_manager.search_vote(user_id, identificador)

            if mode == 'like':
                update_curso_like_count_menos(identificador)
            elif mode == 'deslike':
                update_curso_deslike_count_menos(identificador)

            if vote:
                vote_manager.db.votes.delete_one({'_id': vote['_id']})

            bot.answer_callback_query(callback_query_id=call.id, text=f"Seu {mode} foi removido com sucesso.")
            send_curso_details_new(user_id, identificador, call.message.chat.id, call.message.message_id)
        else:
            logging.warning("Dados insuficientes para remover voto.")
            bot.answer_callback_query(call.id, text="Dados de remoção de voto inválidos.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao remover o voto: {e}")

def add_like_callback_handler(call):
    try:
        user_id = call.from_user.id
        
        data = call.data.split()
        if len(data) >= 2:
            identificador = data[1]
            vote_manager.add_vote(user_id, identificador, 'like')
            bot.answer_callback_query(call.id, text="Você deu like nessa série!")

            update_curso_like_count(identificador)

            send_curso_details_new(user_id, identificador, call.message.chat.id, call.message.message_id)
        else:
            logging.warning("Dados insuficientes para adicionar like.")
            bot.answer_callback_query(call.id, text="Dados de like inválidos.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao adicionar like: {e}")

def add_deslike_callback_handler(call):
    try:
        user_id = call.from_user.id
        data = call.data.split()
        if len(data) >= 2:
            identificador = data[1]
            vote_manager.add_vote(user_id, identificador, 'deslike')
            bot.answer_callback_query(call.id, text="Você deu deslike nessa série!")

            update_curso_deslike_count(identificador)

            send_curso_details_new(user_id, identificador, call.message.chat.id, call.message.message_id)
        else:
            logging.warning("Dados insuficientes para adicionar deslike.")
            bot.answer_callback_query(call.id, text="Dados de deslike inválidos.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao add deslike: {e}")

def add_to_my_fav_list(call):
    try:
        identificador = call.data.split(" ")[-1]

        user_id = call.from_user.id
        user_data = user_manager.search_user(user_id)
        if user_data:
            my_fav_list = user_data.get('my_fav', [])

            if identificador not in my_fav_list:
                user_manager.db.users.update_one(
                    {'user_id': user_id},
                    {'$addToSet': {'my_fav': identificador}}
                )
            else:
                pass
            bot.answer_callback_query(call.id, text="Série adicionada à sua lista.")
            send_curso_details_new(user_id, identificador, call.message.chat.id, call.message.message_id)
        else:
            logging.warning(f"Usuário não encontrado no banco de dados: UserID={user_id}")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao adicionar a série à lista do usuário: {e}")
        bot.answer_callback_query(call.id, text="Ocorreu um erro ao adicionar a série à sua lista. Por favor, tente novamente mais tarde.")

def remove_from_my_fav_list(call):
    try:
        identificador = call.data.split(" ")[-1]

        user_id = call.from_user.id
        user_data = user_manager.search_user(user_id)
        my_fav_list = user_data.get('my_fav', [])

        if identificador in my_fav_list:
            user_manager.db.users.update_one(
                {'user_id': user_id},
                {'$pull': {'my_fav': identificador}}
            )

            bot.answer_callback_query(call.id, text="Série removida da sua lista.")
            send_curso_details_new(user_id, identificador, call.message.chat.id, call.message.message_id)
        else:
            logging.warning(f"ID={identificador} não encontrado na lista de favoritos do UserID={user_id}")
            bot.send_message(user_id, "Série não encontrada na sua lista.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao remover a série da lista do usuário: {e}")
        bot.answer_callback_query(call.id, text="Ocorreu um erro ao remover a série da sua lista. Por favor, tente novamente mais tarde.")


def send_curso_details_new(user_id, idnt, chat_id, message_id):
    try:
        bot.send_chat_action(chat_id, 'upload_photo')
        idnt = str(idnt)
        curso = search_curso_by_id(idnt)
        if curso:
            views = int(curso.get('view', 0))
            total_likes = int(curso.get('like', 0))
            total_dislikes = int(curso.get('deslike', 0))
            like_percentage = 0
            if total_likes + total_dislikes > 0:
                like_percentage = int((total_likes / (total_likes + total_dislikes)) * 100)

            star_rating = ''
            if like_percentage >= 0 and like_percentage < 20:
                star_rating = '⭐️'
            elif like_percentage >= 20 and like_percentage < 40:
                star_rating = '⭐️⭐️'
            elif like_percentage >= 40 and like_percentage < 60:
                star_rating = '⭐️⭐️⭐️'
            elif like_percentage >= 60 and like_percentage < 80:
                star_rating = '⭐️⭐️⭐️⭐️'
            elif like_percentage >= 80 and like_percentage <= 100:
                star_rating = '⭐️⭐️⭐️⭐️⭐️'
            else:
                star_rating = '⭐️'

            photo = curso.get('thumb_nail')
            temp = int(curso.get('temp', 0))
            if temp is None:
                temp = 0 

            caption = (
                f"<b>Nome:</b> {curso.get('nome')}\n"
                f"<b>Lançamento:</b> {curso.get('lanc')}\n"
                f"<b>Duração:</b> {curso.get('duracao')}\n"
                f"<b>Categoria:</b> {curso.get('categoria')}\n"
                f"<b>Tamanho:</b> {curso.get('tamanho')}\n"
                f"<b>Criador:</b> {curso.get('criado')}\n\n"
                f"<b>Recomendação:</b> {star_rating}\n"
                f"<b>Visualizações:</b> {views}"
            )
            
            user_data = user_manager.search_user(user_id)
            my_fav_list = user_data.get('my_fav', [])
            is_in_my_fav = idnt in my_fav_list

            if is_in_my_fav:
                my_fav_button = types.InlineKeyboardButton("➖ Remover à Minha Lista", callback_data=f"REMOVE_MY_FAV {idnt}")
            else:
                my_fav_button = types.InlineKeyboardButton("➕ Adicionar à Minha Lista", callback_data=f"ADD_MY_FAV {idnt}")

            keyboard = []

            keyboard.append([my_fav_button])
            reply_markup = types.InlineKeyboardMarkup(keyboard)

            vote = vote_manager.search_vote(user_id, idnt)

            if vote:
                mode = vote.get('mode')
                remove_vote_button = types.InlineKeyboardButton("🗑 Remover Voto", callback_data=f"REMOVE_VOTE {idnt} {mode}")
                keyboard.append([remove_vote_button])
            else:
                like_button = types.InlineKeyboardButton("👍 Like", callback_data=f"ADD_LIKE {idnt}")
                deslike_button = types.InlineKeyboardButton("👎 Deslike", callback_data=f"ADD_DESLIKE {idnt}")
                keyboard.append([like_button, deslike_button])

            temp_total = get_temp_total(idnt)

            for temp in range(1, temp_total + 1):
                text = f"▶️ Temporada {temp}"
                callback_data = f"EPISODIO= {idnt} {temp}"  
                button = types.InlineKeyboardButton(text, switch_inline_query_current_chat=callback_data)  # Correção aqui
                keyboard.append([button])


            reply_markup = types.InlineKeyboardMarkup(keyboard) 

            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
                reply_markup=reply_markup
            )
        else:
            logging.error("Curso não encontrada no banco de dados.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")

@bot.message_handler(func=lambda message: message.text.startswith("EPISODIO="))
def handle_epidodio_command(message):
    try:
        text = message.text
        parts = text.split("=")
        args = parts[1].strip().split()
        if len(args) == 3:
                idnt = args[0]
                temp = args[1]
                episodio = args[2]
                send_eps(message, idnt, temp, episodio)
        else:
                bot.reply_to(
                    message, "Formato incorreto. Use 'EPISODIO= {idnt} {temp} {episodio}' para buscar um episódio específico.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")

@bot.message_handler(func=lambda message: message.text.startswith("HISTORICO="))
def handle_epidodio_command(message):
    try:
        text = message.text
        parts = text.split("=")
        args = parts[1].strip().split()
        if len(args) == 3:
                idnt = args[0]
                temp = args[1]
                episodio = args[2]
                send_eps(message, idnt, temp, episodio)
        else:
                bot.reply_to(
                    message, "Formato incorreto. Use 'EPISODIO= {idnt} {temp} {episodio}' para buscar um episódio específico.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")

users_with_string_historico = user_manager.db.users.find({ 'historico': { '$type': 'string' } })

def send_eps(message, idnt, temp, episodio):
    try:
        bot.send_chat_action(message.chat.id, 'upload_video')
        idnt = str(idnt)
        temp = int(temp)
        episodio = int(episodio)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        result = video_manager.db.videos.find_one({"idnt": idnt, "episodio": episodio})
        if result:
            video_manager.db.videos.update_one({"idnt": idnt}, {"$inc": {"view": 1}})
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        is_premium = user_manager.is_premium(user_id)
        if is_premium:
            episodios = video_manager.search_curso(idnt, temp, episodio)
            if episodios:
                episodio_data = episodios[0]  
                caption = (
                    f"<b>Nome:</b> {episodio_data.get('description')}\n"
                    f"<b>Temporada:</b> {episodio_data.get('temp')}\n"
                    f"<b>Episódio:</b> {episodio_data.get('episodio')}\n"
                )
                video_file_id = episodio_data.get('file_id')
                keyboard_play = types.InlineKeyboardMarkup(row_width=3)

                previous_button = types.InlineKeyboardButton(
                    text='⬅️ Anterior', callback_data=f'previous_media {idnt} {temp} {episodio}')
                next_button = types.InlineKeyboardButton(
                    text='➡️ Próximo', callback_data=f'next_media {idnt} {temp} {episodio}')
                more_button = types.InlineKeyboardButton(
                    text='🎬 Episódios', switch_inline_query_current_chat=f"EPISODIO= {idnt} {temp}")
                menu_button = types.InlineKeyboardButton(
                    text='❇️ Menu', callback_data=f"voltar_info={idnt}")
                start_back_button = types.InlineKeyboardButton(
                    text='ℹ️ Início', callback_data='menu_start')
                support_button = types.InlineKeyboardButton(
                    text='🆘 Suporte', url='https://t.me/kylorensbot')

                keyboard_play.add(previous_button, more_button, next_button)
                keyboard_play.add(menu_button, start_back_button)
                keyboard_play.add(support_button)

                bot.send_video(
                    chat_id=message.chat.id,
                    video=video_file_id,
                    parse_mode="HTML",
                    caption=caption,
                    reply_markup=keyboard_play
                )  
                user_manager.add_to_historico(user_id, idnt, temp, episodio)
            else:              
                bot.reply_to(message, "Nenhum episódio encontrado com os parâmetros fornecidos.")
        else:
            reply_markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton(text="🎫 Assinatura", callback_data="comprar")
            reply_markup.row(back_button)
            photo = 'https://i.imgur.com/c3nzNhd.png'
            message_text = "Você precisa adquirir o plano de acesso, clique no botão para saber mais."
            bot.send_photo(message.chat.id, photo, caption=message_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")


def send_eps_bottuan(message, idnt, temp, episodio):
    try:
        chat_id = message.chat.id
        bot.send_chat_action(chat_id, 'upload_video')
        idnt = str(idnt)
        temp = int(temp)
        episodio_num = int(episodio)  
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        user_id = chat_id
        user = user_manager.search_user(user_id)
        episodio_data_list = video_manager.search_curso(idnt, temp, episodio_num)        
        if episodio_data_list and len(episodio_data_list) > 0:
            episodio_data = episodio_data_list[0]
            
            caption = (
                f"<b>Nome:</b> {episodio_data['description']}\n"
                f"<b>Temporada:</b> {episodio_data['temp']}\n"
                f"<b>Episódio:</b> {episodio_data['episodio']}\n"
            )
            video_file_id = episodio_data['file_id']

            keyboard_play = types.InlineKeyboardMarkup(row_width=3)

            previous_button = types.InlineKeyboardButton(
                text='⬅️ Anterior', callback_data=f'previous_media {idnt} {temp} {episodio_num}')
            next_button = types.InlineKeyboardButton(
                text='➡️ Próximo', callback_data=f'next_media {idnt} {temp} {episodio_num}')
            more_button = types.InlineKeyboardButton(
                text='🎬 Episódios', switch_inline_query_current_chat=f"EPISODIO= {idnt} {temp}")
            menu_button = types.InlineKeyboardButton(
                text='❇️ Menu', callback_data=f"voltar_info={idnt}")
            start_back_button = types.InlineKeyboardButton(
                text='ℹ️ Início', callback_data='menu_start')
            support_button = types.InlineKeyboardButton(
                text='🆘 Suporte', url='https://t.me/kylorensbot')

            keyboard_play.add(previous_button, more_button, next_button)
            keyboard_play.add(menu_button, start_back_button)
            keyboard_play.add(support_button)

            bot.send_video(
                chat_id=message.chat.id,
                video=video_file_id,
                parse_mode="HTML",
                caption=caption,
                reply_markup=keyboard_play
            )  
            user_manager.add_to_historico(chat_id, idnt, temp, episodio_num)

        else:              
            bot.reply_to(message, "Nenhum episódio encontrado com os parâmetros fornecidos.")
    except Exception as e:
        logging.error(f"Error in send_eps_bottuan: {e}")


def get_total_episodes(idnt, temp):
    try:
        idnt = str(idnt)
        temp = int(temp)
        
        video_total = video_manager.db.videos.count_documents({
            "idnt": idnt,
            "temp": temp
        })
        return video_total
    
    except Exception as e:
        logging.error(f"Error in get_total_episodes: {e}")
        return 0  


def previous_media_callback(call):
    try:
        
        _, idnt, temp, episodio = call.data.split()
        idnt = str(idnt)
        temp = int(temp)
        episodio = int(episodio)
        chat_id = call.message.chat.id
        
        previous_eps = episodio - 1
        user_id = call.from_user.id 
        user = user_manager.search_user(user_id)

        if user and user.get('premium') == 'true':
            if previous_eps >= 1:
                bot.send_chat_action(call.message.chat.id, 'upload_video')
                send_eps_bottuan(call.message, idnt, temp, previous_eps)
            else:
                bot.answer_callback_query(call.id, text="Você já está no primeiro episódio", show_alert=True)
        else:
            reply_markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton(text="🎫 Assinatura", callback_data="comprar")
            reply_markup.row(back_button)
            photo = 'https://i.imgur.com/c3nzNhd.png'
            message_text = "Você precisa adquirir o plano de acesso, clique no botão para saber mais."
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=call.message.message_id, 
                media=telebot.types.InputMediaPhoto(photo, caption=message_text, parse_mode="HTML"),
                reply_markup=reply_markup
            )
    except Exception as e:
        logging.error(f"Error in previous_media_callback: {e}")

def next_media_callback(call):
    try:
        _, idnt, temp, episodio = call.data.split()
        idnt = str(idnt)
        temp = int(temp)
        episodio = int(episodio)
        chat_id = call.message.chat.id

        next_eps = episodio + 1
        total_eps = get_total_episodes(idnt, temp) 
        user_id = call.from_user.id 
        user = user_manager.search_user(user_id)
        if user and user.get('premium') == 'true':
            if next_eps <= total_eps:  
                bot.send_chat_action(call.message.chat.id, 'upload_video')
                send_eps_bottuan(call.message, idnt, temp, next_eps)
            else:
                bot.answer_callback_query(call.id, text="Você já está no último episódio", show_alert=True)
        else:
            reply_markup = telebot.types.InlineKeyboardMarkup()
            back_button = telebot.types.InlineKeyboardButton(text="🎫 Assinatura", callback_data="comprar")
            reply_markup.row(back_button)
            photo = 'https://i.imgur.com/c3nzNhd.png'
            message_text = "Você precisa adquirir o plano de acesso, clique no botão para saber."
            bot.edit_message_media(
                 chat_id=chat_id,
                 message_id=call.message.message_id, 
                 media=telebot.types.InputMediaPhoto(photo, caption=message_text, parse_mode="HTML"),
                 reply_markup=reply_markup
                 )
            
    except Exception as e:
        logging.error(f"Error in next_media_callback: {e}")


def menu_curso_callback(call):
    chat_id = call.message.chat.id

    try:
        bot.send_chat_action(call.message, 'upload_photo')
        idnt = call.data.split('=')[1]
        idnt = str(idnt)
        curso = video_manager.search_videos_idnt(idnt)
        if curso:
            caption = (
                f"<b>Nome:</b> {curso.get('nome')}\n"
                f"<b>Lançamento:</b> {curso.get('lanc')}\n"
                f"<b>Duração:</b> {curso.get('duracao')}\n"
                f"<b>Categoria:</b> {curso.get('categoria')}\n\n"
                f"<b>Tamanho:</b> {curso.get('tamanho')}\n\n"
                f"<b>Criador:</b> {curso.get('criado')}\n\n"
            )

            photo = curso.get('thumb_nail')
            temp = int(curso.get('temp'))
            identificador = curso.get('idnt')
            nome = curso.get('nome')

            keyboard = []
            
            temp_total = get_temp_total(idnt)
            for temp in range(1, temp_total + 1):
                text = f"▶️ Temporada {temp}"
                callback_data = f"EPISODIO= {identificador} {temp}"  
                button = types.InlineKeyboardButton(text, switch_inline_query_current_chat=callback_data)
                keyboard.append([button])

            reply_markup = types.InlineKeyboardMarkup(keyboard)

            bot.edit_message_media(
                chat_id=chat_id,
                message_id=call.message.message_id,
                media=telebot.types.InputMediaPhoto(photo, caption=caption, parse_mode="HTML"),
                reply_markup=reply_markup,
            )
        else:
            bot.send_message(chat_id, "Curso não encontrada no banco de dados.")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar os detalhes do curso: {e}")

@bot.message_handler(commands=['sdb'])
def cursos_dados(message):
    if message.chat.type == "private":
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        if user and user.get("sudo") == "true":
            if len(message.text.split()) != 2:
                bot.send_message(message.chat.id, "Uso incorreto. Use /sdb file_id")
                return
            file_id = message.text.split()[1]

            curso = video_manager.db.videos.find_one({'file_id': file_id})
            if not curso:
                bot.send_message(message.chat.id, "File ID não encontrado no banco de dados.")
                return

            bot.send_message(message.chat.id, "Digite o idnt do curso:")
            bot.register_next_step_handler(message, get_idnt, curso, file_id)

def get_idnt(message, curso, file_id):
    idnt = message.text
    curso['file_id'] = file_id  

    curso_existente = video_manager.db.videos.find_one({'idnt': idnt})
    
    if curso_existente:
        ultimo_curso = video_manager.db.videos.find({'idnt': idnt}).sort('message_id', -1).limit(1)
        if ultimo_curso and 'thumb_nail' in ultimo_curso[0]:
            curso['thumb_nail'] = ultimo_curso[0]['thumb_nail']
        curso['idnt'] = idnt

        bot.send_message(message.chat.id, "IDNT e File ID já existem. Agora insira as seguintes informações para atualização:")
        bot.send_message(message.chat.id, "Digite a nova descrição:")
        bot.register_next_step_handler(message, get_description_existing, curso)
    else:
        curso['idnt'] = idnt
        bot.send_message(message.chat.id, "IDNT não encontrado ou File ID diferente. Vamos adicionar um novo curso.")
        bot.send_message(message.chat.id, "Digite o NOME do curso:")
        bot.register_next_step_handler(message, get_nome_new, curso)

# Quando o IDNT e File ID já existem
def get_description_existing(message, curso):
    description = message.text
    curso['description'] = description
    bot.send_message(message.chat.id, "Digite a temporada do curso:")
    bot.register_next_step_handler(message, get_temp_existing, curso)

def get_temp_existing(message, curso):
    temp = message.text
    curso['temp'] = int(temp)
    bot.send_message(message.chat.id, "Digite o episódio do curso:")
    bot.register_next_step_handler(message, get_episode_existing, curso)

def get_episode_existing(message, curso):
    episodio = message.text
    curso['episodio'] = int(episodio)

    # Atualiza o documento com base em idnt e file_id
    video_manager.db.videos.update_one(
        {'file_id': curso['file_id']},
        {'$set': curso, }
    )
    curso_atualizado = video_manager.db.videos.find_one({'file_id': curso['file_id']})
    curso_info = (
        f"📚 <b>Curso Atualizado com Sucesso!</b>\n\n"
        f"<b>IDNT:</b> <code>{curso_atualizado['idnt']}</code>\n"
        f"<b>Nome:</b> {curso_atualizado['nome']}\n"
        f"<b>Descrição:</b> {curso_atualizado['description']}\n"
        f"<b>Temporada:</b> {curso_atualizado['temp']}\n"
        f"<b>Episódio:</b> {curso_atualizado['episodio']}\n"
        f"<b>Total de Vídeos:</b> {curso_atualizado.get('video_total', 'N/A')}\n"
        f"<b>Data de Lançamento:</b> {curso_atualizado.get('lanc', 'N/A')}\n"
        f"<b>Duração:</b> {curso_atualizado.get('duracao', 'N/A')}\n"
        f"<b>Categoria:</b> {curso_atualizado.get('categoria', 'N/A')}\n"
        f"<b>Tamanho:</b> {curso_atualizado.get('tamanho', 'N/A')} MB\n"
        f"<b>Criado por:</b> {curso_atualizado.get('criado', 'N/A')}\n"
        f"<b>Thumn_nail:</b> {curso_atualizado.get('thumb_nail', 'N/A')}\n"
        f"<b>Visualizações:</b> {curso_atualizado.get('view', 0)}\n"
        f"<b>Likes:</b> {curso_atualizado.get('like', 0)}\n"
        f"<b>Deslikes:</b> {curso_atualizado.get('deslike', 0)}"
    )

    bot.send_message(message.chat.id, curso_info, parse_mode='HTML')

# Quando o IDNT não existe ou o File ID é diferente e estamos adicionando um novo curso
def get_nome_new(message, curso):
    nome = message.text
    curso['nome'] = nome
    bot.send_message(message.chat.id, "Digite a descrição do curso:")
    bot.register_next_step_handler(message, get_description_new, curso)

def get_description_new(message, curso):
    description = message.text
    curso['description'] = description
    bot.send_message(message.chat.id, "Digite o total de vídeos do curso:")
    bot.register_next_step_handler(message, get_video_total_new, curso)

def get_video_total_new(message, curso):
    video_total = message.text
    curso['video_total'] = int(video_total)
    bot.send_message(message.chat.id, "Digite a data de lançamento do curso:")
    bot.register_next_step_handler(message, get_lanc_new, curso)

def get_lanc_new(message, curso):
    lanc = message.text
    curso['lanc'] = int(lanc)
    bot.send_message(message.chat.id, "Digite a duração do curso:")
    bot.register_next_step_handler(message, get_duracao_new, curso)

def get_duracao_new(message, curso):
    duracao = message.text
    curso['duracao'] = duracao
    bot.send_message(message.chat.id, "Digite a temporada do curso:")
    bot.register_next_step_handler(message, get_temp_new, curso)

def get_temp_new(message, curso):
    temp = message.text
    curso['temp'] = int(temp)
    bot.send_message(message.chat.id, "Digite o episódio do curso:")
    bot.register_next_step_handler(message, get_episode_new, curso)

def get_episode_new(message, curso):
    episodio = message.text
    curso['episodio'] = int(episodio)
    bot.send_message(message.chat.id, "Digite a categoria do curso:")
    bot.register_next_step_handler(message, get_category_new, curso)

def get_category_new(message, curso):
    categoria = message.text
    curso['categoria'] = categoria
    bot.send_message(message.chat.id, "Digite o tamanho do curso (MB):")
    bot.register_next_step_handler(message, get_size_new, curso)

def get_size_new(message, curso):
    tamanho = message.text
    curso['tamanho'] = int(tamanho)
    bot.send_message(message.chat.id, "Digite o nome do criador do curso:")
    bot.register_next_step_handler(message, get_criado_new, curso)

def get_criado_new(message, curso):
    criado = message.text
    curso['criado'] = criado
    bot.send_message(message.chat.id, "Digite o URL Thumb_nail do curso:")
    bot.register_next_step_handler(message, get_thumb_new, curso)

def get_thumb_new(message, curso):
    thumb_nail_url = message.text
    curso['thumb_nail'] = thumb_nail_url

    # Adiciona um novo documento no banco de dados
    video_manager.db.videos.update_one(
            {'file_id': curso['file_id']},
            {'$set': curso}
        )
    curso_atualizado = video_manager.db.videos.find_one({'file_id': curso['file_id']})
    curso_info = (
        f"📚 <b>Curso Atualizado com Sucesso!</b>\n\n"
        f"<b>IDNT:</b> <code>{curso_atualizado['idnt']}</code>\n"
        f"<b>Nome:</b> {curso_atualizado['nome']}\n"
        f"<b>Descrição:</b> {curso_atualizado['description']}\n"
        f"<b>Temporada:</b> {curso_atualizado['temp']}\n"
        f"<b>Episódio:</b> {curso_atualizado['episodio']}\n"
        f"<b>Total de Vídeos:</b> {curso_atualizado.get('video_total', 'N/A')}\n"
        f"<b>Data de Lançamento:</b> {curso_atualizado.get('lanc', 'N/A')}\n"
        f"<b>Duração:</b> {curso_atualizado.get('duracao', 'N/A')}\n"
        f"<b>Categoria:</b> {curso_atualizado.get('categoria', 'N/A')}\n"
        f"<b>Tamanho:</b> {curso_atualizado.get('tamanho', 'N/A')} MB\n"
        f"<b>Criado por:</b> {curso_atualizado.get('criado', 'N/A')}\n"
        f"<b>Thumn_nail:</b> {curso_atualizado.get('thumb_nail', 'N/A')}\n"
        f"<b>Visualizações:</b> {curso_atualizado.get('view', 0)}\n"
        f"<b>Likes:</b> {curso_atualizado.get('like', 0)}\n"
        f"<b>Deslikes:</b> {curso_atualizado.get('deslike', 0)}"
    )

    bot.send_message(message.chat.id, curso_info, parse_mode='HTML')

@bot.message_handler(commands=['check_video'])
def check_video(message):
    if message.chat.type == "private":
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        if user and user.get("sudo") == "true":
                args = message.text.split()
        if len(args) != 4:  
                bot.send_message(message.chat.id, "Uso incorreto. Use /check_video idnt temp eps")
                return
            
        idnt = args[1]
        temp = int(args[2])
        eps = int(args[3])
        curso_atualizado = video_manager.db.videos.find_one({
                'idnt': idnt,
                'temp': temp,
                'episodio': eps
            })

        if not curso_atualizado:
                bot.send_message(message.chat.id, "🔍 Curso não encontrado com os dados fornecidos.")
                return

        curso_info = (
                f"📚 <b>Informações do Curso:</b>\n\n"
                f"<b>IDNT:</b> <code>{curso_atualizado['idnt']}</code>\n"
                f"<b>Nome:</b> {curso_atualizado['nome']}\n"
                f"<b>Descrição:</b> {curso_atualizado['description']}\n"
                f"<b>Temporada:</b> {curso_atualizado['temp']}\n"
                f"<b>Episódio:</b> {curso_atualizado['episodio']}\n"
                f"<b>Total de Vídeos:</b> {curso_atualizado.get('video_total', 'N/A')}\n"
                f"<b>Data de Lançamento:</b> {curso_atualizado.get('lanc', 'N/A')}\n"
                f"<b>Duração:</b> {curso_atualizado.get('duracao', 'N/A')}\n"
                f"<b>Categoria:</b> {curso_atualizado.get('categoria', 'N/A')}\n"
                f"<b>Tamanho:</b> {curso_atualizado.get('tamanho', 'N/A')} MB\n"
                f"<b>Criado por:</b> {curso_atualizado.get('criado', 'N/A')}\n"
                f"<b>Thumn_nail:</b> {curso_atualizado.get('thumb_nail', 'N/A')}\n"
                f"<b>Visualizações:</b> {curso_atualizado.get('view', 0)}\n"
                f"<b>Likes:</b> {curso_atualizado.get('like', 0)}\n"
                f"<b>Deslikes:</b> {curso_atualizado.get('deslike', 0)}"
            )

        bot.send_message(message.chat.id, curso_info, parse_mode='HTML')
        
def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Bot iniciado...")
    schedule.every().day.at("00:00").do(verificar_assinaturas)
    schedule.every().sunday.at("18:00").do(send_recommendations)
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    bot.send_message(
            GROUP_LOG_ID,
            f'#{bot.get_me().username} #ONLINE\n\n<b>Bot is on</b>\n\n<b>Version:</b> {cursosbrbot_version}\n<b>Python version:</b> {python_version}\n<b>Lib version:</b> {telebot_version}',
            message_thread_id=43147,
        )
    
    bot.infinity_polling(allowed_updates=util.update_types, timeout=10, long_polling_timeout = 5)
    logging.info("BOT INICIADO COM SUCESSO")