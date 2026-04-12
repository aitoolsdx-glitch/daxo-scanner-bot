import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from groq import Groq

# --- НАСТРОЙКИ (БЕЗОПАСНО) ---
# Теперь бот будет брать ключи из настроек хостинга, а не из текста файла
API_TOKEN = os.getenv('BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446  # Твой ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
client = Groq(api_key=GROQ_API_KEY)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(">> CHIIP System Online\nОтправь мне файл для анализа метаданных.")

@dp.message_handler(content_types=['document'])
async def handle_docs(message: types.Message):
    file_name = message.document.file_name
    await message.answer(f"🔍 Анализирую файл: {file_name}...")
    
    # Промпт для ИИ
    prompt = f"Ты — эксперт по кибербезопасности. Проанализируй файл с названием {file_name}. Напиши вердикт (Низкий/Высокий риск), перечисли возможные угрозы и дай техническое описание. Используй стиль хакерского терминала и эмодзи."
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192", 
        )
        response = chat_completion.choices[0].message.content
        await message.answer(f"📦 **Метаданные файла**\n{response}", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка ИИ: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
