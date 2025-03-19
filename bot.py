import os
import sqlite3
import shutil
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit, ImageReader
from PIL import Image

# 📌 Папки для файлів
PDF_FOLDER = "pdfs"
IMAGE_FOLDER = "images"
FONT_FOLDER = "fonts"
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(FONT_FOLDER, exist_ok=True)

# 📌 Шляхи до файлів
TEXT_FONT_PATH = "DejaVuSans.ttf"
BACKGROUND_IMAGE_PATH = os.path.join("fern_pastel_background.jpg")
DEST_TEXT_FONT_PATH = os.path.join(FONT_FOLDER, "DejaVuSans.ttf")

# 📌 Копіюємо шрифт у папку, якщо його там немає
if not os.path.exists(DEST_TEXT_FONT_PATH):
    shutil.copy(TEXT_FONT_PATH, DEST_TEXT_FONT_PATH)

# 📌 Реєструємо шрифт
pdfmetrics.registerFont(TTFont("DejaVu", DEST_TEXT_FONT_PATH))

# 📌 База даних
DB_FILE = "dairy.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        user_id INTEGER,
        content TEXT,
        type TEXT CHECK(type IN ('text', 'image')),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# 📌 Збереження записів у базу
def save_entry(user_id, content, entry_type="text"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if entry_type == "text":
        content_with_date = f"{timestamp}\n{content}"
        cursor.execute("INSERT INTO entries (user_id, content, type, timestamp) VALUES (?, ?, 'text', ?)",
                       (user_id, content_with_date, timestamp))
    else:
        cursor.execute("INSERT INTO entries (user_id, content, type, timestamp) VALUES (?, ?, 'image', ?)",
                       (user_id, content, timestamp))

    conn.commit()
    conn.close()

# 📌 Збереження фото
def save_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1].get_file()

    user_image_folder = os.path.join(IMAGE_FOLDER, str(user_id))
    os.makedirs(user_image_folder, exist_ok=True)

    image_path = os.path.join(user_image_folder, f"{photo.file_id}.jpg")
    photo.download(image_path)

    save_entry(user_id, image_path, entry_type="image")
    update.message.reply_text("📷 Зображення збережено!")

# 📌 Отримання всіх записів користувача
def get_user_data(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT content, type FROM entries WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

# 📌 Очищення щоденника
def clear_dairy(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    user_image_folder = os.path.join(IMAGE_FOLDER, str(user_id))
    if os.path.exists(user_image_folder):
        shutil.rmtree(user_image_folder)

    update.message.reply_text("🗑 Всі записи та фото видалені! Титульна сторінка збережена.")

# 📌 Створення PDF із фоном, текстом та фото
def create_pdf(user_id):
    user_data = get_user_data(user_id)

    if not user_data:
        return None

    pdf_path = os.path.join(PDF_FOLDER, f"dairy_{user_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 50
    max_width = width - 2 * margin
    y_position = height - margin
    c.setFont("DejaVu", 12)

    # Додаємо титульну сторінку
    bg = ImageReader(BACKGROUND_IMAGE_PATH)
    c.drawImage(bg, 0, 0, width, height)
    c.setFont("DejaVu", 20)
    c.drawCentredString(width / 2, height - 100, "Мій Щоденник")
    c.setFont("DejaVu", 14)
    c.drawCentredString(width / 2, height - 130, f"Дата створення: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    c.showPage()
    c.setFont("DejaVu", 12)

    # Додаємо записи та фото
    c.drawImage(bg, 0, 0, width, height)
    y_position = height - margin

    for content, entry_type in user_data:
        if entry_type == "image":
            if os.path.exists(content):
                img = Image.open(content)
                img.thumbnail((400, 400))
                img_width, img_height = img.size

                if y_position < img_height + margin:
                    c.showPage()
                    c.drawImage(bg, 0, 0, width, height)
                    c.setFont("DejaVu", 12)
                    y_position = height - margin

                x_position = (width - img_width) / 2
                c.drawImage(content, x_position, y_position - img_height, width=img_width, height=img_height)
                y_position -= img_height + 20
        else:
            lines = simpleSplit(content, "DejaVu", 12, max_width)
            for line in lines:
                if y_position < 100:
                    c.showPage()
                    c.drawImage(bg, 0, 0, width, height)
                    c.setFont("DejaVu", 12)
                    y_position = height - margin
                c.drawString(margin, y_position, line)
                y_position -= 18

    c.save()
    return pdf_path

# 📌 Обробник команди /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 Привіт! Надсилай текст або фото. Введи /pdf, щоб отримати свої записи у PDF. Використовуй /clear_dairy для очищення записів.")

# 📌 Обробник текстових повідомлень
def dairy(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text
    save_entry(user_id, text)
    update.message.reply_text("✅ Запис збережено!")

# 📌 Обробник команди /pdf (надсилання PDF)
def send_pdf(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    pdf_path = create_pdf(user_id)

    if pdf_path and os.path.exists(pdf_path):
        update.message.reply_document(document=open(pdf_path, "rb"), filename="Мій_щоденник.pdf")
    else:
        update.message.reply_text("ℹ У тебе ще немає записів.")

# 📌 Запуск бота
def main():
    init_db()
    import os
    TOKEN = "7643345132:AAGKqyJx64-gatYkBSzqRXnBf1qgIqsKsU0"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("pdf", send_pdf))
    dp.add_handler(CommandHandler("clear_dairy", clear_dairy))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, dairy))
    dp.add_handler(MessageHandler(Filters.photo, save_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()