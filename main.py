import asyncio
import os
import pytz
from datetime import datetime, time, timedelta, date
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from groq import Groq
from fastapi import FastAPI, Response
import uvicorn
import threading

# 🔑 Ключи из переменных окружения (безопасно!)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_KEY")

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или GROQ_KEY в переменных окружения!")

# Инициализация
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

# Часовой пояс: Новосибирск
TZ = pytz.timezone('Asia/Novosibirsk')

# Хранилище пользователей и статистики
user_chat_ids = set()
stats = {"date": date.today(), "godzilla": 0, "plushe": 0}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Кормление"), KeyboardButton(text="🚽 Туалет")],
            [KeyboardButton(text="🎓 Команды"), KeyboardButton(text="💤 Режим")],
            [KeyboardButton(text="🧸 Плюша"), KeyboardButton(text="👹 Годзилла / Кракен")],
            [KeyboardButton(text="⏰ Тест напоминания"), KeyboardButton(text="❓ Спросить ИИ")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_chat_ids.add(message.chat.id)
    await message.answer(
        "🐾 Привет! Я — Чип, цифровой помощник для Альмы!\n\n"
        "✨ Каждый день в 20:30 (Новосибирск) напомню потренировать команды\n"
        "🧸 Жми «Плюша», когда Альма ласковая и спокойная\n"
        "👹 Жми «Годзилла / Кракен», когда жуёт пелёнки или буянит 😼\n"
        "🍽🚽🎓💤 — советы по воспитанию от ИИ\n\n"
        "Давайте вместе воспитаем самую умную мальтипу! 🐩💕",
        reply_markup=get_main_keyboard()
    )

async def send_training_reminder():
    if not user_chat_ids:
        print("⚠️ Нет пользователей для напоминания")
        return
    
    today_g = stats["godzilla"]
    today_p = stats["plushe"]
    ratio_text = f"\n📊 Сегодня Альма была Плюшей {today_p} раз и Годзиллой {today_g} раз — молодцы! 🌈" if (today_g + today_p) > 0 else ""
    
    message_text = (
        "🔔 Время тренировки команд с Альмой!\n\n"
        "Сегодня потренируйте:\n"
        "• «Сидеть» — 3 раза с лакомством\n"
        "• «Ко мне» — позовите с 2 метров\n"
        "• «Место» — у лежанки 1 минута\n\n"
        "Всего 5-7 минут — и Альма станет умнее! 🐩✨"
        f"{ratio_text}"
    )
    
    for chat_id in user_chat_ids:
        try:
            await bot.send_message(chat_id, message_text)
            print(f"✅ Напоминание отправлено в {chat_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки в {chat_id}: {e}")

async def daily_reminder_task():
    while True:
        now = datetime.now(TZ)
        target_time = TZ.localize(datetime.combine(now.date(), time(20, 30)))
        if now >= target_time:
            target_time += timedelta(days=1)
        seconds_until = (target_time - now).total_seconds()
        print(f"⏰ Следующее напоминание в 20:30 по Новосибирску ({int(seconds_until/60)} мин осталось)")
        await asyncio.sleep(seconds_until)
        await send_training_reminder()
        await asyncio.sleep(10)

@dp.message(F.text == "⏰ Тест напоминания")
async def test_reminder_handler(message: Message):
    user_chat_ids.add(message.chat.id)
    await send_training_reminder()
    await message.answer("✅ Тестовое напоминание отправлено!", reply_markup=get_main_keyboard())

@dp.message(F.text == "🧸 Плюша")
async def plushe_handler(message: Message):
    global stats
    if stats["date"] != date.today():
        stats["date"] = date.today()
        stats["godzilla"] = 0
        stats["plushe"] = 0
    stats["plushe"] += 1
    count = stats["plushe"]
    responses = [
        f"🧸 Альма сегодня Плюша уже {count} раз! Как же она мила, когда спокойная 😻",
        f"✨ Плюшевый режим активирован! Альма лежит как ангел — {count} раз за сегодня. Настя, смотри! 💕",
        f"💤 Альма сегодня {count}-й раз показала, что умеет быть тихой и ласковой. Это повод для гордости! 🐩",
        f"🌈 Плюшевая Альма №{count}! Такие моменты — ради них всё и затевалось, правда? 😊",
        f"🌟 Сегодня Альма уже {count} раз была нежной Плюшей. Запечатлей этот момент — завтра снова будет Годзилла 😼"
    ]
    response = responses[count % len(responses)]
    await message.answer(f"{response}\n\n💡 P.S. Гладь Альму в такие моменты — она запоминает, что спокойствие = любовь ❤️", reply_markup=get_main_keyboard())

@dp.message(F.text == "👹 Годзилла / Кракен")
async def godzilla_handler(message: Message):
    global stats
    if stats["date"] != date.today():
        stats["date"] = date.today()
        stats["godzilla"] = 0
        stats["plushe"] = 0
    stats["godzilla"] += 1
    count = stats["godzilla"]
    responses = [
        f"👹 Годзилла-режим активирован! Альма сегодня уже {count} раз напомнила, что она не Плюша 😼\nНо это нормально — щенки исследуют мир зубами!",
        f"🐙 Кракен поднялся со дна! Шкода №{count} засчитана.\nСовет: отвлеки Альму игрушкой-жвачкой — и пелёнка снова в безопасности 🌊",
        f"💥 Атака Годзиллы №{count}! Обнаружены следы разорванных пелёнок.\nНе ругайте — просто замени на новую и дай игрушку. Через месяц Альма поймёт разницу!",
        f"🌪️ Торнадо по имени Альма бушует! Это шкода №{count} за сегодня.\nЗапомните: чем спокойнее вы — тем быстрее Альма научится границам 🧘",
        f"🦕 Динозавр Альма сегодня уже {count} раз напомнил: «Я щенок, мне можно!»\nНа самом деле — не совсем можно, но терпение победит! Через 2 месяца будет тише 🙏"
    ]
    response = responses[count % len(responses)]
    await message.answer(f"{response}\n\n💡 P.S. После шкоды — 5 минут тишины и ласки. Альма не вредничает, она просто учится!", reply_markup=get_main_keyboard())

@dp.message(F.text.in_({"🍽 Кормление", "🚽 Туалет", "🎓 Команды", "💤 Режим"}))
async def button_handler(message: Message):
    topic_map = {
        "🍽 Кормление": "Сколько раз в день кормить щенка 2-6 месяцев? Какие продукты запрещены?",
        "🚽 Туалет": "Как приучить щенка 2-4 месяцев ходить в туалет на пелёнку? Сколько раз сажать? Почему щенок жуёт пелёнку?",
        "🎓 Команды": "Как научить щенка командам 'сидеть' и 'ко мне' без наказаний?",
        "💤 Режим": "Сколько должен спать щенок 3-5 месяцев? Как приучить к лежанке?"
    }
    await message.answer("⏳ Генерирую совет через ИИ (5-10 сек)...")
    try:
        resp = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты — кинолог с 15-летним стажем. Отвечай кратко, практично, на русском."},
                {"role": "user", "content": topic_map[message.text]}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=400
        )
        await message.answer(f"💡 {message.text}\n\n{resp.choices[0].message.content}", reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка Groq: {str(e)[:200]}", reply_markup=get_main_keyboard())

@dp.message(F.text == "❓ Спросить ИИ")
async def ask_ai_handler(message: Message):
    await message.answer("✏️ Напиши свой вопрос про Альму:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Отмена")]], resize_keyboard=True))

@dp.message(F.text == "🔙 Отмена")
async def cancel_handler(message: Message):
    await start_handler(message)

@dp.message()
async def fallback_handler(message: Message):
    if message.text.startswith('/'):
        return
    await message.answer("🧠 Думаю...")
    try:
        resp = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты — добрый кинолог. Отвечай только о собаках/щенках. Если вопрос не по теме — вежливо откажись."},
                {"role": "user", "content": message.text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500
        )
        await message.answer(f"🐶 Ответ ИИ:\n\n{resp.choices[0].message.content}", reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:200]}", reply_markup=get_main_keyboard())

# FastAPI для "пробуждения" через HTTP
app = FastAPI()

@app.get("/")
async def health_check():
    return {"status": "healthy", "message": "Бот жив! 🐩"}

@app.head("/")
async def health_check_head():
    return Response(status_code=200)

@app.get("/wake")
async def wake():
    return {"status": "awake", "message": "Чип на связи! 🌰"}

@app.head("/wake")
async def wake_head():
    return Response(status_code=200)

async def start_bot():
    asyncio.create_task(daily_reminder_task())
    print("✅ Бот запущен (24/7 на Render + UptimeRobot)")
    print(f"⏰ Напоминания в 20:30 по Новосибирску (UTC+7)")
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем FastAPI сервер на порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
