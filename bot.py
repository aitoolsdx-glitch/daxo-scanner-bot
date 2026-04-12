import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq

# Ключи из настроек Render
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(">> CHIIP System Online\nОтправь мне файл для анализа метаданных.")

@dp.message()
async def handle_everything(message: types.Message):
    # Проверяем, есть ли документ или текст
    name = message.document.file_name if message.document else "сообщение"
    await message.answer(f"🔍 Анализирую: {name}...")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Ты ИИ CHIIP. Проанализируй кратко: {name}"}],
            model="llama3-8b-8192",
        )
        await message.answer(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
