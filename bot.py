"""
Telegram-бот для отслеживания режима дня и питания.
Автор: создано с Claude для Елены.

Функции:
- Сон (отбой/подъём)
- Приёмы пищи
- Вода
- Настроение / энергия
- Активность
- Ежедневная сводка
- История в SQLite
"""

import logging
import sqlite3
from datetime import datetime, date

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ===================== НАСТРОЙКИ =====================

BOT_TOKEN = "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"  # получишь у @BotFather в Telegram
DB_PATH = "daily_tracker.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Состояния для диалогов (ConversationHandler)
(
    MEAL_TEXT,
    WATER_AMOUNT,
    MOOD_SCORE,
    ENERGY_SCORE,
    ACTIVITY_TEXT,
    SLEEP_BEDTIME,
    SLEEP_WAKETIME,
) = range(7)

# ===================== БАЗА ДАННЫХ =====================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            value TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_entry(user_id: int, entry_type: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = date.today().isoformat()
    now = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO entries (user_id, entry_date, entry_type, value, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, today, entry_type, value, now),
    )
    conn.commit()
    conn.close()


def get_today_entries(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = date.today().isoformat()
    cur.execute(
        "SELECT entry_type, value, created_at FROM entries WHERE user_id = ? AND entry_date = ? ORDER BY created_at",
        (user_id, today),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ===================== КЛАВИАТУРА =====================

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🍽 Приём пищи"), KeyboardButton("💧 Вода")],
        [KeyboardButton("😊 Настроение"), KeyboardButton("⚡ Энергия")],
        [KeyboardButton("🏃 Активность"), KeyboardButton("😴 Сон")],
        [KeyboardButton("📊 Сводка за день")],
    ],
    resize_keyboard=True,
)

CANCEL_KEYBOARD = ReplyKeyboardMarkup([["Отмена"]], resize_keyboard=True)

MOOD_KEYBOARD = ReplyKeyboardMarkup(
    [["1", "2", "3", "4", "5"], ["Отмена"]], resize_keyboard=True
)

# ===================== БАЗОВЫЕ КОМАНДЫ =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🌿 Я твой бот для отслеживания режима дня и питания.\n\n"
        "Выбери, что хочешь записать, на клавиатуре ниже.\n"
        "В любой момент можно посмотреть сводку за сегодня — кнопка «📊 Сводка за день».",
        reply_markup=MAIN_MENU,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== ПРИЁМ ПИЩИ =====================

async def meal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Что ты съела? Напиши коротко (например: «овсянка с ягодами»).",
        reply_markup=CANCEL_KEYBOARD,
    )
    return MEAL_TEXT


async def meal_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_entry(update.effective_user.id, "meal", text)
    await update.message.reply_text(f"Записала: 🍽 {text}", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== ВОДА =====================

async def water_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Сколько воды выпила? (например: 250мл или 1 стакан)",
        reply_markup=CANCEL_KEYBOARD,
    )
    return WATER_AMOUNT


async def water_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_entry(update.effective_user.id, "water", text)
    await update.message.reply_text(f"Записала: 💧 {text}", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== НАСТРОЕНИЕ =====================

async def mood_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оцени настроение от 1 (плохо) до 5 (отлично):",
        reply_markup=MOOD_KEYBOARD,
    )
    return MOOD_SCORE


async def mood_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_entry(update.effective_user.id, "mood", text)
    await update.message.reply_text(f"Записала: 😊 настроение {text}/5", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== ЭНЕРГИЯ =====================

async def energy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оцени уровень энергии от 1 (нет сил) до 5 (полна сил):",
        reply_markup=MOOD_KEYBOARD,
    )
    return ENERGY_SCORE


async def energy_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_entry(update.effective_user.id, "energy", text)
    await update.message.reply_text(f"Записала: ⚡ энергия {text}/5", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== АКТИВНОСТЬ =====================

async def activity_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Какая активность была? (например: «прогулка 30 минут», «йога»)",
        reply_markup=CANCEL_KEYBOARD,
    )
    return ACTIVITY_TEXT


async def activity_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_entry(update.effective_user.id, "activity", text)
    await update.message.reply_text(f"Записала: 🏃 {text}", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== СОН =====================

async def sleep_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Во сколько легла спать? (например: 23:30)",
        reply_markup=CANCEL_KEYBOARD,
    )
    return SLEEP_BEDTIME


async def sleep_bedtime_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bedtime"] = update.message.text
    await update.message.reply_text("Во сколько проснулась? (например: 07:30)")
    return SLEEP_WAKETIME


async def sleep_waketime_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bedtime = context.user_data.get("bedtime", "?")
    waketime = update.message.text
    value = f"отбой {bedtime} → подъём {waketime}"
    add_entry(update.effective_user.id, "sleep", value)
    await update.message.reply_text(f"Записала: 😴 {value}", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ===================== СВОДКА =====================

LABELS = {
    "meal": "🍽 Приём пищи",
    "water": "💧 Вода",
    "mood": "😊 Настроение",
    "energy": "⚡ Энергия",
    "activity": "🏃 Активность",
    "sleep": "😴 Сон",
}


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_today_entries(update.effective_user.id)
    if not rows:
        await update.message.reply_text(
            "Сегодня записей пока нет. Начни с любой кнопки на клавиатуре!",
            reply_markup=MAIN_MENU,
        )
        return

    lines = [f"📊 Сводка за {date.today().strftime('%d.%m.%Y')}:\n"]
    for entry_type, value, created_at in rows:
        time_str = created_at.split("T")[1][:5]
        label = LABELS.get(entry_type, entry_type)
        lines.append(f"{time_str} — {label}: {value}")

    await update.message.reply_text("\n".join(lines), reply_markup=MAIN_MENU)


# ===================== ЗАПУСК =====================

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📊 Сводка за день$"), summary))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🍽 Приём пищи$"), meal_start)],
        states={MEAL_TEXT: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), meal_save)]},
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💧 Вода$"), water_start)],
        states={WATER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), water_save)]},
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^😊 Настроение$"), mood_start)],
        states={MOOD_SCORE: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), mood_save)]},
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚡ Энергия$"), energy_start)],
        states={ENERGY_SCORE: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), energy_save)]},
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏃 Активность$"), activity_start)],
        states={ACTIVITY_TEXT: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), activity_save)]},
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^😴 Сон$"), sleep_start)],
        states={
            SLEEP_BEDTIME: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), sleep_bedtime_save)],
            SLEEP_WAKETIME: [MessageHandler(filters.TEXT & ~filters.Regex("^Отмена$"), sleep_waketime_save)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    ))

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
