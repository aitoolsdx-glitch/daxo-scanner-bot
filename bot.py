import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# --- CONFIG ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
users_db = set()

# --- КНОПКИ ---
def admin_menu():
    kb = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast_info")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db.add(user_id)
        # Уведомление тебе
        try:
            await bot.send_message(ADMIN_ID, f"🆕 **Новый пользователь!**\nID: `{user_id}`\nName: {message.from_user.full_name}")
        except: pass
    await message.answer(">> CHIIP System Online\nПришли текст или файл для анализа.")

@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Админ-панель**\nЮзеров: {len(users_db)}", reply_markup=admin_menu())

@dp.callback_query(F.data == "stats")
async def stats_callback(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Всего пользователей: {len(users_db)}")
    await callback.answer()

@dp.callback_query(F.data == "broadcast_info")
async def broadcast_info(callback: types.CallbackQuery):
    await callback.message.answer("Для рассылки напиши: `/send ТвойТекст`")
    await callback.answer()

@dp.message(Command("send"))
async def send_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        if not text: return await message.answer("Введите текст.")
        for u in users_db:
            try: await bot.send_message(u, f"📢 **CHIIP INFO:**\n\n{text}")
            except: pass
        await message.answer("✅ Отправлено")

# АНАЛИЗ ГРОКОМ
@dp.message()
async def analyze_message(message: types.Message):
    # Добавляем в базу
    users_db.add(message.from_user.id)
    
    content = message.text if message.text else "Файл/Медиа объект"
    if message.document:
        content = f"Файл: {message.document.file_name}"
    
    wait_msg = await message.answer("🔍 **CHIIP сканирует...**")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Проведи краткий технический аудит: {content}"}],
            model="llama3-8b-8192",
        )
        await wait_msg.edit_text(f"📦 **Вердикт:**\n{chat_completion.choices[0].message.content}")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка ИИ: {e}")

# --- ВЕБ-СЕРВЕР (ЧТОБЫ RENDER НЕ ВЫКЛЮЧАЛ БОТА) ---
async def handle(request):
    return web.Response(text="CHIIP Status: Online")

async def main():
    # Запуск веб-сервера на порту 10000 (стандарт Render)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())