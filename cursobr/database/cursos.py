from ..database.db_connection import DBConnection
import re

class VideoManager:
    """Classe responsável por gerenciar a coleção de vídeos no banco de dados."""

    def __init__(self):
        """Inicializa a conexão com o banco de dados usando DBConnection."""
        self.db_connection = DBConnection()
        self.db = self.db_connection.get_db()

    def search_video(self, file_id):
        """Busca um vídeo no banco de dados pelo file_id."""
        return self.db.videos.find_one({"file_id": file_id})

    def search_videos_idnt(self, idnt):
        """Busca um vídeo no banco de dados pelo file_id."""
        return self.db.videos.find_one({"idnt": idnt})
    
    def search_by_year(self, ano):
        """Busca um vídeo no banco de dados pelo file_id."""
        return self.db.videos.find_one({"lanc": {"$regex": f"^{re.escape(ano)}$", "$options": "i"}})
    
    
    def search_genero(self, genero):
        """Busca cursos pelo gênero no banco de dados."""
        return list(self.db.videos.find({"genero": {"$regex": f"^{re.escape(genero)}$", "$options": "i"}}))

    def search_cursos_id(self, id):
        """Busca um vídeo no banco de dados pelo id."""
        return self.db.videos.find_one({"id": id})
    
    def search_curso(self, identificador, temporada, episodio):
        return list(self.db.videos.find({
            "idnt": str(identificador),
            "temp": int(temporada),
            'episodio': int(episodio)
    }))
    
    def add_filme_db(self, message):
        """Adiciona um novo vídeo ao banco de dados."""
        last_video = self.db.videos.find().sort("id", -1).limit(1)
        last_video = list(last_video)
        
        if len(last_video) == 0:
            new_id = 1
        else:
            last_id = last_video[0]['id']
            new_id = int(last_id) + 1

        result = self.db.videos.insert_one({
            'id': new_id,
            'idnt': '',
            'chat_id': message.chat.id,
            'message_id': message.message_id,
            'content_type': message.content_type,
            'file_id': message.video.file_id,
            'description': message.caption or "",
            'video_total': None,
            'nome': '',
            'lanc': None,
            'duracao': '',
            'temp': 1,
            'episodio': 1,
            'categoria': '',
            'tamanho': 20,
            "criado": '',
            'thumb_nail': '',
            'like': 0,
            'deslike': 0,
            'view': 0,
        })
        return result

    def count_videos_by_category(self):
        """Conta a quantidade de vídeos por categoria no banco de dados."""
        pipeline = [
            {"$group": {"_id": "$categoria", "total_videos": {"$sum": 1}}},
            {"$sort": {"total_videos": -1}} 
        ]
        
        categories_count = list(self.db.videos.aggregate(pipeline))
        
        return categories_count
    
    def count_total_videos(self):
        """Conta o total de vídeos no banco de dados."""
        idnt = self.db.videos.count_documents({})
        return idnt

    def count_unique_idnt(self):
        """Conta o número de idnt distintos no banco de dados."""
        unique_idnt_count = len(self.db.videos.distinct('idnt'))
        return unique_idnt_count