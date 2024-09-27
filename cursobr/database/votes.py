from ..database.db_connection import DBConnection
from ..bot.bot import bot

class VoteManager:
    """Classe responsável por gerenciar os votos no banco de dados."""

    def __init__(self):
        """Inicializa a conexão com o banco de dados usando DBConnection."""
        self.db_connection = DBConnection()
        self.db = self.db_connection.get_db()
        
    def search_vote(self, user_id, identificador):
        return self.db.votes.find_one({
                'user_id': user_id,
                'idnt': identificador,
            })


    def add_vote(self, user_id, identificador, mode):
        last_id = self.db.votes.find().sort("id", -1).limit(1)
        last_id = list(last_id)
        
        if len(last_id) == 0:
            new_id = 1
        else:
            last_id = last_id[0]['id']
            new_id = int(last_id) + 1
        self.db.votes.insert_one({
            'id': new_id,
            'user_id': int(user_id),
            'idnt': identificador,
            'mode': mode,
        })
