import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- БЕЗОПАСНОЕ ПОЛУЧЕНИЕ КЛЮЧЕЙ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446

if not TOKEN or not GROQ_KEY:
    print("❌ ОШИБКА: Переменные BOT_TOKEN или GROQ_KEY не найдены в Environment Variables!")

bot = Bot(token=TOKEN) if TOKEN else None
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
users_db = set()

# --- КНОПКИ ---
def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="prep_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db.add(user_id)
        try:
            # Уведомление админу
            await bot.send_message(ADMIN_ID, f"🆕 **Новый пользователь!**\nID: `{user_id}`\nИмя: {message.from_user.full_name}")
        except Exception: pass
    await message.answer(">> CHIIP System Online\nОтправь текст или файл для анализа.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Панель управления**\nЮзеров: {len(users_db)}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "stats")
async def call_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Юзеров в базе: {len(users_db)}")
    await callback.answer()

@dp.callback_query(F.data == "prep_broadcast")
async def call_broadcast(callback: types.CallbackQuery):
    await callback.message.answer("Используй: `/send ТЕКСТ` для рассылки.")
    await callback.answer()

@dp.message(Command("send"))
async def cmd_send_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        if not text: return await message.answer("Напиши текст сообщения.")
        count = 0
        for u in users_db:
            try:
                await bot.send_message(u, f"📢 **Рассылка:**\n\n{text}")
                count += 1
            except Exception: pass
        await message.answer(f"✅ Отправлено: {count}")

@dp.message()
async def analyze_handler(message: types.Message):
    users_db.add(message.from_user.id)
    
    # Определяем контент для нейросети
    input_content = ""
    if message.document:
        input_content = f"Файл с названием: {message.document.file_name}"
    elif message.text:
        input_content = message.text
    else:
        input_content = "Неизвестный тип данных (возможно, фото или стикер)"

    status_msg = await message.answer("🔍 **CHIIP сканирует...**")
    
    try:
        if not client:
            raise Exception("GROQ_KEY не настроен")
            
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Проведи быстрый анализ и дай вердикт: {input_content}"}],
            model="llama3-8b-8192",
        )
        await status_msg.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка анализа: {str(e)}")

# --- KEEP-ALIVE SERVER ---
async def handle_web(request):
    return web.Response(text="CHIIP Status: Online")

async def main():
    if not bot:
        print("❌ Бот не запущен: отсутствует токен.")
        return

    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server started on port {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())