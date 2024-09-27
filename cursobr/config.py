import configparser
import os

script_directory = os.path.dirname(os.path.abspath(__file__))
bot_conf_path = os.path.join(script_directory, "..", "bot.conf")

config = configparser.ConfigParser()
config.read(bot_conf_path)


BOT_TOKEN = config['BOT']['TOKEN']
MONGO_CON = config['DB']['MONGO_CON']
CHANNEL_ID = config['BOT']['cursos_CHANNEL']
GROUP_LOG_ID = config['BOT']['cursos_GROUP']
BOT_OWNER_ID = int(config['BOT']['OWNER_ID'])
STORAGE_ID = int(config['BOT']['cursos_ARMAZENAMENTO'])
PAYMENT_POST_ID = int(config['BOT']['cursos_POST_PAGAMENTO'])
