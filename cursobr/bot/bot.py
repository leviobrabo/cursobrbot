import telebot
from ..config import BOT_TOKEN
from ..database.db_connection import DBConnection
from cursobr.loggers import logging

logging.info('INICIANDO CONEXÃO COM O MONGODB')
DBConnection()
logging.info('Conexão com o MongoDB estabelecida com sucesso!')

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

