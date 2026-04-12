import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq
from aiohttp import web

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446  # Твой ID (проверь в боте @userinfobot если не уверен)

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)

# База данных в памяти (для примера)
users = set()

# --- КЛАВИАТУРА АДМИНКИ ---
def get_admin_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats"))
    builder.row(types.InlineKeyboardButton(text="📢 Рассылка (тест)", callback_data="broadcast"))
    builder.row(types.InlineKeyboardButton(text="⚙️ Перезагрузить ИИ", callback_data="reboot_ai"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users.add(message.from_user.id)
    await message.answer(">> CHIIP System Online\nБот готов. Отправь сообщение для анализа.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 **Панель управления CHIIP**", reply_markup=get_admin_kb())
    else:
        await message.answer("🛑 Доступ заблокирован. У вас нет прав администратора.")

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.message.edit_text(f"📈 **Статистика системы:**\n\nВсего пользователей: {len(users)}\nСтатус ИИ: Работает (Groq Llama-3)")
    await callback.answer()

@dp.message()
async def handle_ai(message: types.Message):
    users.add(message.from_user.id)
    msg = await message.answer("🔍 Анализ...")
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text or "Анализ данных"}],
            model="llama3-8b-8192",
        )
        await msg.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_render(request):
    return web.Response(text="Bot is running")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_render)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
