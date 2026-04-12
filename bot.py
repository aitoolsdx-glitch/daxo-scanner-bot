import os
import asyncio
from aiogram import Bot, Dispatcher, types
from groq import Groq
from aiohttp import web

# --- CONFIG ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
users_db = set()

# --- КНОПКИ ---
def get_admin_kb():
    # Прямой импорт типов для кнопок
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="prep_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---

# Обработка команд /start и /admin через обычный регистратор
@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Регистрация нового юзера
    if user_id not in users_db:
        users_db.add(user_id)
        try:
            await bot.send_message(ADMIN_ID, f"🆕 **Новый пользователь!**\nID: `{user_id}`\nИмя: {message.from_user.full_name}")
        except: pass

    # Команда START
    if message.text == "/start":
        return await message.answer(">> CHIIP System Online\nОтправь файл или текст для анализа.")

    # Команда ADMIN
    if message.text == "/admin" and user_id == ADMIN_ID:
        return await message.answer(f"🛠 **Панель CHIIP**\nЮзеров: {len(users_db)}", reply_markup=get_admin_kb())

    # Команда SEND (Рассылка)
    if message.text and message.text.startswith("/send") and user_id == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        if not text: return await message.answer("Напиши текст.")
        count = 0
        for u in users_db:
            try:
                await bot.send_message(u, f"📢 **Сообщение:**\n\n{text}")
                count += 1
            except: pass
        return await message.answer(f"✅ Отправлено: {count}")

    # ЕСЛИ ЭТО НЕ КОМАНДА — ЗНАЧИТ АНАЛИЗИРУЕМ
    status = await message.answer("🔍 **CHIIP анализирует...**")
    
    content = ""
    if message.document:
        content = f"Файл: {message.document.file_name}"
    elif message.text:
        content = message.text
    else:
        content = "Неизвестный тип данных"

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Сделай краткий аудит безопасности: {content}"}],
            model="llama3-8b-8192",
        )
        await status.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await status.edit_text(f"❌ Ошибка ИИ: {e}")

# ОБРАБОТКА КНОПОК
@dp.callback_query()
async def process_callbacks(callback: types.CallbackQuery):
    if callback.data == "stats":
        await callback.message.answer(f"📈 Юзеров в сессии: {len(users_db)}")
    elif callback.data == "prep_broadcast":
        await callback.message.answer("Пиши: `/send ТвойТекст`")
    await callback.answer()

# --- СЕРВЕР RENDER ---
async def handle_web(request):
    return web.Response(text="CHIIP Status: Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())