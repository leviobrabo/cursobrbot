from ..config import BOT_OWNER_ID, GROUP_LOG_ID
from ..database.users import UserManager
from ..bot.bot import bot

user_manager = UserManager()

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if message.chat.type == "private":
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        if user and user.get("sudo") == "true":
            if len(message.text.split()) == 2:
                ban_user_id = int(message.text.split()[1])
                ban_user = user_manager.search_user(ban_user_id)
                if ban_user:
                    if ban_user.get("banned") == "true":
                        bot.send_message(message.chat.id, "Este usuário já foi banido anteriormente.")
                    elif ban_user.get("sudo") == "true":
                        bot.send_message(message.chat.id, "Você não pode banir um usuário com permissão de sudo.")
                    else:
                        result = user_manager.db.users.update_one({"user_id": ban_user_id}, {"$set": {"banned": "true"}})
                        if result.modified_count > 0:
                            if message.from_user.username:
                                username = "@" + message.from_user.username
                            else:
                                username = "Não tem um nome de usuário"
                            updated_user = user_manager.db.users.find_one({"user_id": ban_user_id})
                            if updated_user:
                                bot.send_message(message.chat.id, f"<b>Usuário banido</b>\n\n<b>ID:</b> <code>{ban_user_id}</code>\n<b>nome:</b> {updated_user.get('name')}\n<b>Username: {username}")
                                bot.send_message(GROUP_LOG_ID, f"<b>#{BOT_OWNER_ID} #user_banned</b>\n<b>ID:</b> <code>{user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username: {username}")
                            else:
                                bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
                else:
                    bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
            else:
                bot.send_message(message.chat.id, "Por favor, forneça um ID de usuário após /ban.")
        else:
            bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if message.chat.type == "private":
        user_id = message.from_user.id
        user = user_manager.search_user(user_id)
        if user and user.get("sudo") == "true":
            if len(message.text.split()) == 2:
                unban_user_id = int(message.text.split()[1])
                unban_user = user_manager.search_user(unban_user_id)
                if unban_user:
                    if unban_user.get("banned") == "false":
                        bot.send_message(message.chat.id, "Este usuário já não está banido.")
                    elif unban_user.get("sudo") == "true":
                        bot.send_message(message.chat.id, "Você não pode desbanir um usuário com permissão de sudo.")
                    else:
                        result = user_manager.db.users.update_one({"user_id": unban_user_id}, {"$set": {"banned": "false"}})
                        if result.modified_count > 0:
                            if message.from_user.username:
                                username = "@" + message.from_user.username
                            else:
                                username = "Não tem um nome de usuário"
                            updated_user = user_manager.db.users.find_one({"user_id": unban_user_id})
                            if updated_user:
                                bot.send_message(message.chat.id, f"<b>Usuário uban</b>\n\n<code>{unban_user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username:</b> {username}")
                                bot.send_message(GROUP_LOG_ID, f"<b>#{BOT_OWNER_ID} #User_unbanned</b>\n<b>ID:</b> <code>{user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username:</b> {username}")
                            else:
                                bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
                else:
                    bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
            else:
                bot.send_message(message.chat.id, "Por favor, forneça um ID de usuário após /unban.")
        else:
            bot.send_message(message.chat.id, "Você não tem permissão para usar este comando.")
