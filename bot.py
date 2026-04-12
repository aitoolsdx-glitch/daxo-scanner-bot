import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq
from aiohttp import web

# Логирование для отслеживания ошибок в консоли Render
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
ADMIN_ID = 5476069446

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_KEY)

# База данных пользователей (в памяти)
users_db = set()

# --- КНОПКИ АДМИНКИ ---
def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="prep_send")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ (HANDLERS) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db.add(user_id)
        # Уведомление админу о новом пользователе
        try:
            await bot.send_message(
                ADMIN_ID, 
                f"🆕 **Новый пользователь!**\n👤: {message.from_user.full_name}\n🆔: `{user_id}`\n🔗: @{message.from_user.username}"
            )
        except: pass
    
    await message.answer(">> CHIIP System Online\nПришли текст или документ для мгновенного анализа безопасности.")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"🛠 **Панель управления CHIIP**\nЮзеров онлайн: {len(users_db)}", reply_markup=get_admin_kb())

@dp.callback_query(F.data == "stats")
async def callback_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📈 Всего уникальных пользователей: {len(users_db)}")
    await callback.answer()

@dp.callback_query(F.data == "prep_send")
async def callback_prep(callback: types.CallbackQuery):
    await callback.message.answer("Чтобы отправить сообщение всем, напиши:\n`/send Твой текст` (например: /send Бот обновлен!)")
    await callback.answer()

@dp.message(Command("send"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        # Извлекаем текст после команды /send
        broadcast_text = message.text.replace("/send", "").strip()
        if not broadcast_text:
            return await message.answer("❌ Ошибка: введи текст сообщения.")
        
        success = 0
        for uid in users_db:
            try:
                await bot.send_message(uid, f"📢 **Сообщение от CHIIP:**\n\n{broadcast_text}")
                success += 1
            except: pass
        await message.answer(f"✅ Рассылка завершена. Получили: {success} чел.")

# Основной обработчик анализа (текст и файлы)
@dp.message()
async def analyze_handler(message: types.Message):
    users_db.add(message.from_user.id)
    
    # Определяем, что за контент
    if message.document:
        target = f"Файл: {message.document.file_name}"
    elif message.text:
        target = message.text
    else:
        return

    wait_msg = await message.answer("🔍 **CHIIP сканирует пакет данных...**")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Сделай экспертный отчет по безопасности для: {target}. Стиль: хакерский терминал."}],
            model="llama3-8b-8192",
        )
        await wait_msg.edit_text(f"📦 **Вердикт:**\n{completion.choices[0].message.content}")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка нейросети: {str(e)}")

# --- ВЕБ-СЕРВЕР (KEEP-ALIVE) ---
async def handle_web(request):
    return web.Response(text="CHIIP Status: Active")

async def main():
    # Запуск веб-сервера для Render
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