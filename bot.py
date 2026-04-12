import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
users = set()

# --- КЛАВИАТУРА АДМИНКИ ---
admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
    [InlineKeyboardButton(text="⚙️ Статус ИИ", callback_data="ai_status")]
])

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users.add(message.from_user.id)
    await message.answer(">> CHIIP System Online\nЖду файл для анализа.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 **Панель управления CHIIP**", reply_markup=admin_kb)
    else:
        await message.answer("🛑 Доступ заблокирован.")

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.message.edit_text(f"📈 **Статистика:**\nЮзеров в базе: {len(users)}")
    await callback.answer()

@dp.message()
async def handle_msg(message: types.Message):
    users.add(message.from_user.id)
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text or "Анализ"}],
            model="llama3-8b-8192",
        )
        await message.answer(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_render(request):
    return web.Response(text="Bot is running")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())