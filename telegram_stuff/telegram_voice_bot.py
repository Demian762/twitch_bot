import winsound
import os
import tempfile
import warnings
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from telegram_stuff.ffmpeg_manager import FFmpegManager
from telegram_stuff.audio_converter import AudioConverter

warnings.filterwarnings("ignore", category=UserWarning, module="telegram")


class TelegramVoiceBot:
    def __init__(self, token, target_chat_id=None):
        self.token = token
        self.target_chat_id = target_chat_id
        self.app = Application.builder().token(self.token).build()  # Crear aquí una sola vez
        self.ffmpeg_manager = FFmpegManager()
        self.converter = AudioConverter(self.ffmpeg_manager.get_ffmpeg_path())
        self.temp_files = []
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.voice:
            return
        
        if self.target_chat_id and update.message.chat.id != self.target_chat_id:
            return
        
        try:
            voice_file = await update.message.voice.get_file()
            temp_ogg = os.path.join(tempfile.gettempdir(), f"voice_{voice_file.file_unique_id}.ogg")
            
            await voice_file.download_to_drive(temp_ogg)
            self.temp_files.append(temp_ogg)
            
            wav_file = self.converter.convert_opus_to_wav(temp_ogg)
            
            if wav_file:
                self.temp_files.append(wav_file)
                winsound.PlaySound(wav_file, winsound.SND_FILENAME)
        except:
            pass
    
    async def start_async(self):
        self.app = Application.builder().token(self.token).build()  # Crear aquí
        
        if self.target_chat_id:
            handler = MessageHandler(filters.VOICE & filters.Chat(self.target_chat_id), self.handle_voice_message)
        else:
            handler = MessageHandler(filters.VOICE, self.handle_voice_message)
        
        self.app.add_handler(handler)
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
    
    async def start_async(self):
        self.app = Application.builder().token(self.token).build()
        
        if self.target_chat_id:
            handler = MessageHandler(filters.VOICE & filters.Chat(self.target_chat_id), self.handle_voice_message)
        else:
            handler = MessageHandler(filters.VOICE, self.handle_voice_message)
        
        self.app.add_handler(handler)
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
    
    def cleanup(self):
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except:
                pass
        self.temp_files.clear()