import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 6265715875 

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
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
            await bot.send_message(ADMIN_ID, f"🆕 **Новый пользователь!**\nID: `{user_id}`\nИмя: {message.from_user.full_name}")
        except: pass
    await message.answer(">> CHIIP System Online\nОтправь файл или текст для анализа.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Панель CHIIP**\nЮзеров в сессии: {len(users_db)}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "stats")
async def call_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Всего уникальных пользователей: {len(users_db)}")
    await callback.answer()

@dp.callback_query(F.data == "prep_broadcast")
async def call_broadcast(callback: types.CallbackQuery):
    await callback.message.answer("Используй: `/send ТЕКСТ` для рассылки.")
    await callback.answer()

@dp.message(Command("send"))
async def cmd_send_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        if not text: return await message.answer("Напиши текст после команды.")
        count = 0
        for u in users_db:
            try:
                await bot.send_message(u, f"📢 **Рассылка от админа:**\n\n{text}")
                count += 1
            except: pass
        await message.answer(f"✅ Отправлено: {count}")

@dp.message()
async def analyze(message: types.Message):
    users_db.add(message.from_user.id)
    
    # Логика определения контента
    if message.document:
        content = f"Файл: {message.document.file_name}"
    elif message.text:
        content = message.text
    else:
        content = "Объект без текста"

    status = await message.answer("🔍 **CHIIP анализирует...**")
    try:
        # Используем Groq для анализа
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Краткий аудит безопасности объекта: {content}"}],
            model="llama3-8b-8192",
        )
        await status.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await status.edit_text(f"❌ Ошибка ИИ: {e}")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_web(request):
    return web.Response(text="CHIIP Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())