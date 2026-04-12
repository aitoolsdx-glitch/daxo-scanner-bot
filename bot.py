import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# Настройка логов, чтобы видеть ошибки в Render
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446  # Твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
users_db = set()

# --- КЛАВИАТУРА АДМИНА ---
def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="prep_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    if user.id not in users_db:
        users_db.add(user_id := user.id)
        # УВЕДОМЛЕНИЕ АДМИНУ
        try:
            await bot.send_message(
                ADMIN_ID, 
                f"🔔 **Новый боец в системе!**\n👤 Имя: {user.full_name}\n🆔 ID: `{user.id}`\n🔗 User: @{user.username or 'нет'}"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу: {e}")
            
    await message.answer(f"Привет, {user.first_name}! >> CHIIP Online.\nПришли текст или файл для анализа.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Панель CHIIP**\nЮзеров в базе: {len(users_db)}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "stats")
async def call_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Статистика сессии: {len(users_db)} пользователей.")
    await callback.answer()

@dp.message(Command("send"))
async def cmd_send_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        if not text: return await message.answer("Напиши: `/send Привет всем`.")
        count = 0
        for u_id in users_db:
            try:
                await bot.send_message(u_id, f"📢 **Внимание! Сообщение от CHIIP:**\n\n{text}")
                count += 1
            except: pass
        await message.answer(f"✅ Рассылка завершена. Получили: {count}")

@dp.message()
async def handle_everything(message: types.Message):
    # Добавляем ID в базу при любой активности
    users_db.add(message.from_user.id)
    
    # Определяем, что нам прислали
    content = ""
    if message.document:
        content = f"Анализ файла: {message.document.file_name}"
    elif message.text:
        content = message.text
    else:
        return # Игнорируем стикеры и прочее

    status_msg = await message.answer("🔍 **CHIIP анализирует...**")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Сделай краткий экспертный отчет (стиль киберпанк): {content}"}],
            model="llama3-8b-8192",
        )
        await status_msg.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка ИИ: {e}")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_render(request):
    return web.Response(text="CHIIP Status: 200 OK")

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