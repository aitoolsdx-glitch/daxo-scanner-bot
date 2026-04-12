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

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)
users_db = set() # Храним ID пользователей здесь

# --- KEYBOARDS ---
def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="prepare_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db.add(user_id)
        # Уведомляем тебя о новом «клиенте»
        await bot.send_message(ADMIN_ID, f"🆕 **Новый пользователь!**\nID: `{user_id}`\nИмя: {message.from_user.full_name}\nUser: @{message.from_user.username}")
    
    await message.answer(">> CHIIP System Online\nОтправь файл или текст для мгновенного анализа безопасности.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Панель управления CHIIP**\nВсего юзеров: {len(users_db)}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "stats")
async def call_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Всего уникальных пользователей: {len(users_db)}")
    await callback.answer()

@dp.callback_query(F.data == "prepare_broadcast")
async def call_broadcast(callback: types.CallbackQuery):
    await callback.message.answer("Чтобы сделать рассылку, напиши команду:\n`/send ТЕКСТ` (вместо ТЕКСТ напиши свое сообщение)")
    await callback.answer()

@dp.message(Command("send"))
async def cmd_send_all(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text_to_send = message.text.replace("/send", "").strip()
        if not text_to_send:
            return await message.answer("Ошибка: напиши текст после команды /send")
        
        count = 0
        for user in users_db:
            try:
                await bot.send_message(user, f"📢 **Сообщение от CHIIP:**\n\n{text_to_send}")
                count += 1
            except: pass
        await message.answer(f"✅ Рассылка завершена. Получили: {count} чел.")

# --- УНИВЕРСАЛЬНЫЙ АНАЛИЗ (ФАЙЛЫ + ТЕКСТ) ---
@dp.message()
async def analyze_everything(message: types.Message):
    users_db.add(message.from_user.id) # Добавляем в базу, если еще нет
    
    # Определяем, что прислали
    if message.document:
        target = f"Файл: {message.document.file_name}"
    elif message.text:
        target = f"Текст: {message.text[:50]}..."
    else:
        target = "Неизвестный объект"

    status_msg = await message.answer("🔍 **CHIIP сканирует объект...**")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Сделай экспертный отчет по безопасности для: {target}. Используй стиль кибер-терминала."}],
            model="llama3-8b-8192",
        )
        await status_msg.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Критическая ошибка ИИ: {e}")

# --- WEB SERVER FOR RENDER ---
async def handle_web(request):
    return web.Response(text="CHIIP Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())