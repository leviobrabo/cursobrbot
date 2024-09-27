from ..config import BOT_OWNER_ID, GROUP_LOG_ID
from ..database.users import UserManager
from ..bot.bot import bot

user_manager = UserManager()

@bot.message_handler(commands=['sudo'])
def sudo_command(message):
    if message.chat.type == "private" and message.from_user.id == BOT_OWNER_ID:
        if len(message.text.split()) == 2:
            user_id = int(message.text.split()[1])
            user = user_manager.search_user(user_id)
            if user:
                if user.get("sudo") == "true":
                    bot.send_message(message.chat.id, "Este usuário já tem permissão de sudo.")
                elif user.get("banned") == "true":
                    bot.send_message(message.chat.id, "Você não pode conceder permissão de sudo a um usuário banido.")
                else:
                    result = user_manager.db.users.update_one({"user_id": user_id}, {"$set": {"sudo": "true"}})
                    if result.modified_count > 0:
                        if message.from_user.username:
                                username = "@" + message.from_user.username
                        else:
                                username = "Não tem um nome de usuário"
                        updated_user = user_manager.db.users.find_one({"user_id": user_id})
                        if updated_user:
                            bot.send_message(message.chat.id, f"<b>Novo sudo adicionado com sucesso</b>\n\n<b>ID:</b> <code>{user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username:</b> {username}")
                            bot.send_message(GROUP_LOG_ID, f"<b>#{bot.get_me().first_name} #New_sudo</b>\n<b>ID:</b> <code>{user_id}</code>\n<b>Name:</b> {updated_user.get('name')}\nU<b>sername:</b> {username}")
                    else:
                        bot.send_message(message.chat.id, "User not found in the database.")
            else:
                bot.send_message(message.chat.id, "User not found in the database.")
        else:
            bot.send_message(message.chat.id, "Por favor, forneça um ID de usuário após /sudo.")

@bot.message_handler(commands=['unsudo'])
def unsudo_command(message):
    if message.chat.type == "private" and message.from_user.id == BOT_OWNER_ID:
        if len(message.text.split()) == 2:
            user_id = int(message.text.split()[1])
            user = user_manager.search_user(user_id)
            if user:
                if user.get("sudo") == "false":
                    bot.send_message(message.chat.id, "Este usuário já não tem permissão de sudo.")
                else:
                    result = user_manager.db.users.update_one({"user_id": user_id}, {"$set": {"sudo": "false"}})
                    if result.modified_count > 0:
                        if message.from_user.username:
                                username = "@" + message.from_user.username
                        else:
                                username = "Não tem um nome de usuário"
                        updated_user = user_manager.db.users.find_one({"user_id": user_id})
                        if updated_user:
                            bot.send_message(message.chat.id, f"<b>User sudo removido com sucesso</b>\n\n<b>ID:</b> <code>{user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username:</b> {username}")
                            bot.send_message(GROUP_LOG_ID, f"<b>#{bot.get_me().first_name} #Rem_sudo</b>\n<b>ID:</b> <code>{user_id}</code>\n<b>Nome:</b> {updated_user.get('name')}\n<b>Username:</b> {username}")
                    else:
                        bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
            else:
                bot.send_message(message.chat.id, "Usuário não encontrado no banco de dados.")
        else:
            bot.send_message(message.chat.id, "Por favor, forneça um ID de usuário após /unsudo.")
