import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Токен берётся из переменной окружения BOT_TOKEN (задаётся в Railway → Variables)
TOKEN = os.environ["BOT_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Проценты от массы продукта: соль, сахар, уксус
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Что вы солите?", reply_markup=main_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    product_key = query.data
    if product_key not in PRODUCTS:
        return

    context.user_data["product"] = product_key
    await query.edit_message_text(
        f"Вы выбрали: {PRODUCTS[product_key]['name']}\n\n"
        "Сколько грамм еды вы солите? (напишите число, например 568)"
    )


async def handle_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    product_key = context.user_data.get("product")

    if not product_key:
        await update.message.reply_text(
            "Сначала выберите продукт:", reply_markup=main_keyboard()
        )
        return

    text = update.message.text.strip().replace(",", ".")
    try:
        weight = float(text)
        if weight <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите положительное число, например 568."
        )
        return

    product = PRODUCTS[product_key]
    lines = [f"📦 {product['name']}, {weight:g} г\n"]
    lines.append(f"🧂 Соль: {weight * product['salt'] / 100:.1f} г")

    if "sugar" in product:
        lines.append(f"🍬 Сахар: {weight * product['sugar'] / 100:.1f} г")
    if "vinegar" in product:
        lines.append(f"🧪 Уксус: {weight * product['vinegar'] / 100:.1f} г")

    lines.append("\nЧтобы начать заново, нажмите /start")

    context.user_data.clear()
    await update.message.reply_text("\n".join(lines))


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weight))
    app.run_polling()


if __name__ == "__main__":
    main()
