import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler

from telegram import (
    Bot,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

TOKEN = os.environ["8925941714:AAHxH9sJf7Qq41A4pkE5ZrCr9WK3R2WvW5o"]

PRODUCTS = {
    "onion": {"name": "Маринованный лук", "salt": 2.0, "sugar": 3.5, "vinegar": 5.0},
    "shashlik": {"name": "Шашлык", "salt": 1.3},
    "meat": {"name": "Мясо", "salt": 1.2},
    "mushrooms": {"name": "Шампики", "salt": 1.2},
    "regular": {"name": "Обычная еда", "salt": 1.0},
}


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧅 Маринованный лук", callback_data="onion")],
        [InlineKeyboardButton("🍢 Шашлык", callback_data="shashlik")],
        [InlineKeyboardButton("🥩 Мясо", callback_data="meat")],
        [InlineKeyboardButton("🍄 Шампиньоны", callback_data="mushrooms")],
        [InlineKeyboardButton("🍽 Обычная еда", callback_data="regular")],
    ])


async def process(data: dict) -> None:
    async with Bot(TOKEN) as bot:
        update = Update.de_json(data, bot)

        # Нажатие на кнопку выбора продукта
        if update.callback_query:
            q = update.callback_query
            await bot.answer_callback_query(q.id)
            if q.data in PRODUCTS:
                await bot.send_message(
                    q.message.chat_id,
                    f"Вы выбрали: {PRODUCTS[q.data]['name']}\n\n"
                    "Сколько грамм еды вы солите? (напишите число, например 568)",
                    reply_markup=ForceReply(input_field_placeholder="568"),
                )
            return

        msg = update.message
        if not msg or not msg.text:
            return
        chat_id = msg.chat_id

        if msg.text.startswith("/start"):
            await bot.send_message(
                chat_id, "Привет! Что вы солите?", reply_markup=main_keyboard()
            )
            return

        # Определяем продукт по сообщению, на которое ответил пользователь
        product = None
        replied = msg.reply_to_message
        if replied and replied.text:
            first_line = replied.text.split("\n")[0]
            for p in PRODUCTS.values():
                if first_line == f"Вы выбрали: {p['name']}":
                    product = p
                    break

        if not product:
            await bot.send_message(
                chat_id, "Сначала выберите продукт:", reply_markup=main_keyboard()
            )
            return

        try:
            weight = float(msg.text.strip().replace(",", "."))
            if weight <= 0:
                raise ValueError
        except ValueError:
            await bot.send_message(
                chat_id,
                f"Вы выбрали: {product['name']}\n\n"
                "Пожалуйста, введите положительное число, например 568.",
                reply_markup=ForceReply(input_field_placeholder="568"),
            )
            return

        lines = [f"📦 {product['name']}, {weight:g} г\n"]
        lines.append(f"🧂 Соль: {weight * product['salt'] / 100:.1f} г")
        if "sugar" in product:
            lines.append(f"🍬 Сахар: {weight * product['sugar'] / 100:.1f} г")
        if "vinegar" in product:
            lines.append(f"🧪 Уксус: {weight * product['vinegar'] / 100:.1f} г")
        lines.append("\nЧтобы начать заново, нажмите /start")
        await bot.send_message(chat_id, "\n".join(lines))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        data = json.loads(self.rfile.read(length))
        try:
            asyncio.run(process(data))
        except Exception as e:
            print("Error:", e)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")