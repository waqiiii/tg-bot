from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === Google Sheets настройки ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    r"/etc/secrets/google_key.json", scope)
client = gspread.authorize(creds)

# ✅ Открытие таблицы по имени
try:
    sheet = client.open("Заявки от пользователей").sheet1
except Exception as e:
    print(f"❌ Не удалось открыть Google Таблицу: {e}")
    exit(1)

# === Telegram настройки ===
ADMIN_CHAT_ID = 7457091820  # Ваш Telegram ID
BOT_TOKEN = "7543607143:AAE5toh_vR9MpzobDta0xfdRh8qEMlkMfYw"

app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ассаламу алайкум! Шерзод Сайдалиевнинг шахсий ёрдамчисиман😇\n\n"
        "Сизга қандай ёрдам беришимиз мумкин? Саволингиз бўлса, марҳамат, Сизга тез орада жавоб берамиз!"
    )

# === Обработка сообщений от пользователей ===
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    now = datetime.now().strftime("%d.%m.%y %H:%M:%S")

    # Сохраняем в Google Sheets
    try:
        sheet.append_row([
            now,
            user.id,
            user.username or "",
            "Сообщение от пользователя",
            text
        ])
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при записи в таблицу.")
        print(f"[Google Sheets ошибка] {e}")
        return

    # Подтверждение пользователю
    await update.message.reply_text("Мурожаатингизни қабул қилдик. \n\nТез орада жавоб берамиз😇")

    # Пересылаем админу
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📨 Сообщение от @{user.username or user.first_name} (ID: {user.id}):\n\n{text}"
    )

# === Обработка ответов от админа ===
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_text = update.message.reply_to_message.text
        if "ID:" in original_text:
            try:
                user_id = int(original_text.split("ID:")[1].split(")")[0])
                reply_text = update.message.text
                now = datetime.now().strftime("%d.%m.%y %H:%M:%S")

                # Отправляем пользователю
                await context.bot.send_message(chat_id=user_id, text=f"💬 Жавоб:\n{reply_text}")

                # Записываем ответ в таблицу
                sheet.append_row([
                    now,
                    update.message.from_user.id,
                    update.message.from_user.username,
                    "Ответ администратора",
                    reply_text
                ])
            except Exception as e:
                await update.message.reply_text("❌ Не удалось отправить или записать ответ.")
                print(f"[Ошибка ответа] {e}")
        else:
            await update.message.reply_text("⚠️ Не найден ID пользователя.")
    else:
        await update.message.reply_text("ℹ️ Ответьте на сообщение пользователя, чтобы ответ дошёл.")

# === Регистрация обработчиков ===
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_CHAT_ID), handle_user_message))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_CHAT_ID), handle_admin_reply))

# === Запуск бота ===
print("✅ Бот запущен!")
app.run_polling()
