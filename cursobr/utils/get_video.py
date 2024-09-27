from ..bot.bot import bot
from ..config import STORAGE_ID, BOT_OWNER_ID
from ..database.cursos import VideoManager

video_manager = VideoManager()

@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_channel_posts(message):
    if message.chat.id == STORAGE_ID:
        if message.content_type == 'video':
            video_caption = message.caption
            video_file_id = message.video.file_id
            video_manager.add_filme_db(message)
            print(f"Armazenado com sucesso no db: {video_file_id}")
            bot.send_message(STORAGE_ID, f'Armazenada com sucesso ✅\n\n<b>Nome:</b> {video_caption}\n<b>File_id:</b> <code>{video_file_id}</code>')
            bot.send_message(BOT_OWNER_ID, f'Armazenada com sucesso ✅\n\n<b>Nome:</b> {video_caption}\n<b>File_id:</b> <code>{video_file_id}</code>')
   
