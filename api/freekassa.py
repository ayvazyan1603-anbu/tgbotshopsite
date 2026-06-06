import json
import hashlib
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

# НАСТРОЙКИ
SECRET_2 = "ЗДЕСЬ_ТВОЙ_СЕКРЕТНЫЙ_КЛЮЧ_2"  # Второй ключ из FreeKassa
BOT_TOKEN = "ЗДЕСЬ_ТОКЕН_ТВОЕГО_ТГ_БОТА"  # Токен твоего бота из @BotFather

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Читаем данные от FreeKassa
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Парсим x-www-form-urlencoded данные
            data = {k: v[0] for k, v in parse_qs(post_data).items()}
            
            merchant_id = data.get('MERCHANT_ID')
            amount = data.get('AMOUNT')
            merchant_order_id = data.get('MERCHANT_ORDER_ID')  # Здесь будет TG ID юзера
            fk_sign = data.get('SIGN')

            # 1. Проверяем подпись FreeKassa
            sign_string = f"{merchant_id}:{amount}:{SECRET_2}:{merchant_order_id}"
            my_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

            if my_sign.lower() != fk_sign.lower():
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"bad sign")
                return

            # 2. Передаем инфу об оплате напрямую в Telegram-бота через API
            # Мы отправим боту админ-запрос, чтобы он переслал сообщение юзеру и начислил звёзды
            user_id = merchant_order_id
            text_message = (
                f"🎉 **Успешная оплата!**\n\n"
                f"Ваш платеж на сумму **{amount} руб.** успешно обработан.\n"
                f"Внутриплатформенные единицы (Stars) зачислены!"
            )
            
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": user_id,
                "text": text_message,
                "parse_mode": "Markdown"
            }
            
            # Отправляем запрос в Телеграм
            requests.post(telegram_url, json=payload)

            # 3. Отвечаем FreeKassa "YES", как она требует
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"YES")

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode('utf-8'))