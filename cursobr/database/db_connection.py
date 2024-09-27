from pymongo import MongoClient

from ..config import MONGO_CON
import logging

class DBConnection:
    """Classe responsável por gerenciar a conexão com o MongoDB."""

    def __init__(self):
        try:
            self.client = MongoClient(MONGO_CON)  
            self.db = self.client.cursobrbot  
        except Exception as e:
            logging.error(f'Erro ao conectar ao MongoDB: {e}')

    def get_db(self):
        """Retorna a instância do banco de dados."""
        return self.db
