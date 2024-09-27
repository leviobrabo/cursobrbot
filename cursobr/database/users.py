from ..database.db_connection import DBConnection
from ..bot.bot import bot
from datetime import datetime, timedelta

class UserManager:
    """Classe responsável por gerenciar os usuários no banco de dados."""

    def __init__(self):
        """Inicializa a conexão com o banco de dados usando DBConnection."""
        self.db_connection = DBConnection()
        self.db = self.db_connection.get_db()

    def search_user(self, user_id):
        """Busca um usuário no banco de dados pelo ID."""
        return self.db.users.find_one({"user_id": user_id})

    def add_user_db(self, message):
        """Adiciona um novo usuário ao banco de dados."""
        first_name = message.from_user.first_name
        last_name = str(message.from_user.last_name).replace('None', '')
        username = str(message.from_user.username).replace("None", "")
        initial_date = datetime.now()
        final_date = initial_date + timedelta(hours=2)

        return self.db.users.insert_one({
            'user_id': message.from_user.id,
            'first_name': f'{first_name} {last_name}',
            "username": username,
            'premium': 'true',
            'initial_date': initial_date.strftime('%Y-%m-%d %H:%M:%S'),
            'final_date': final_date.strftime('%Y-%m-%d %H:%M:%S'),
            'sudo': 'false',
            'banned': 'false',
            'indicado': '',
            'indicacao': 0,
            'favorite': '',
            'my_fav': [],
            'historico': '',
        })
        # falta criar o historico (ultimo video acessado pelo usuario)

    def get_all_users(self, query=None):
        """
        Retorna todos os usuários do banco de dados.
        Se query for fornecida, será usada para filtrar os resultados.
        """
        return list(self.db.users.find({}))


    def update_user_info(self, user_id, key, value):
        """Atualiza informações de um usuário."""
        try:
            value = value.replace('None', '')
        except AttributeError:
            pass
        return self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {key: value}},
        )

    def is_team_member(self, user_id, CHANNEL_ID):
        """Verifica se o usuário faz parte do time."""
        if bot.get_chat_member(CHANNEL_ID, user_id).status == 'left':
            return False
        return True

    def is_premium(self, user_id):
        """Verifica se o usuário é premium."""
        user = self.search_user(user_id)  
        if user and user.get('premium') == 'true':
            return True
        return False

    def is_banned(self, user_id):
        """Verifica se o usuário está banido."""
        user = self.search_user(user_id)  
        if user and user.get('banned') == 'true':
            return True
        return False

    def is_sudo(self, user_id):
        """Verifica se o usuário tem privilégios de sudo."""
        user = self.search_user(user_id)  
        if user and user.get('sudo') == 'true':
            return True
        return False

    def update_user_indicado(self, user_id, indicador_id):
        """Atualiza o usuário com o ID do indicador."""
        indicador_id = int(indicador_id)
        self.db.users.update_one({"user_id": user_id}, {"$set": {"indicado": indicador_id}})

    def update_user_indicacao(self, user_id):
        """Incrementa o campo 'indicacao' de um usuário em 1."""
        self.db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"indicacao": 1}}
        )


    def add_to_historico(self, user_id, idnt, temp, episodio):
        """Atualiza o campo 'historico' com o último vídeo acessado."""
        historico_str = f"{idnt} {temp} {episodio}"
        self.db.users.update_one(
            {'user_id': user_id},
            {'$set': {'historico': historico_str}}  
        )
