import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from groq import Groq

# Получаем ключи из настроек Render
API_TOKEN = os.getenv('BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_KEY')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY)

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer(">> CHIIP System Online\nОтправь мне файл для анализа метаданных.")

@dp.message(F.document)
async def handle_docs(message: types.Message):
    file_name = message.document.file_name
    await message.answer(f"🔍 Анализирую: {file_name}...")
    
    prompt = f"Ты — эксперт по кибербезопасности. Проанализируй файл {file_name}. Напиши вердикт в стиле хакерского терминала."
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        response = chat_completion.choices[0].message.content
        await message.answer(f"📦 **Вердикт:**\n{response}")
    except Exception as e:
        await message.answer(f"❌ Ошибка нейросети: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
