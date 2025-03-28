import os
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import os
from datetime import datetime
import pytz
from telegram import ParseMode
import textwrap

def format_datetime_ukr(dt: datetime):
    months_ukr = [
        "січня", "лютого", "березня", "квітня", "травня", "червня",
        "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"
    ]
    return f"{dt.day} {months_ukr[dt.month - 1]} {dt.year}, {dt.strftime('%H:%M')}"

json_path = "data.json"

# Якщо файлу немає — створити з базовою структурою
if not os.path.exists(json_path):
    data = {
        "name": "Користувач",
        "title": "Мій Щоденник Інтуїції",
        "entries": []
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
else:
    # Якщо файл є — завантажити
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

def download_image(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    return None

# Фолдери
DATA_FOLDER = "data"
PDF_FOLDER = "pdf"
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Шляхи до шрифту та фону (використаємо пізніше в PDF)
FONT_PATH = "DejaVuSans.ttf"
BACKGROUND_IMAGE = "paporot.jpg"

# Запитання
MORNING_QUESTIONS = [
    "☀️ Як я сьогодні прокинулась/прокинувся?",
    "✨ Який перший образ або думка з’явилася після пробудження?",
    "🍵 Що мені хочеться сьогодні для тіла?",
    "❤️ Який мій настрій зараз?",
    "📓 Що мені хочеться сьогодні зробити перш за все?",
    "💡 Яке головне бажання на цей день?",
    "🔍 На що я хочу звернути увагу сьогодні?",
    "🌿 Чого я хочу уникнути сьогодні?",
    "🔥 Що надихає мене цього ранку?",
    "☕ Чого потребує моя душа сьогодні?",
    "🧘 Як я можу підтримати свій емоційний стан?",
    "🕊️ Чи хочу я сьогодні тиші чи руху?",
    "🎨 У який колір я б пофарбувала/пофарбував свій день?",
    "📖 Яка історія сьогоднішнього дня хоче бути написана?",
    "⏳ Що важливо встигнути сьогодні саме для мене?",
    "🧩 Який внутрішній пазл хоче скластися сьогодні?",
    "🌈 Як я можу додати більше радості у свій день?",
    "🎯 Який мій особистий фокус на сьогодні?",
    "🎈 Чим я можу себе потішити сьогодні?",
    "🌬️ Що мені варто відпустити з ранку?",
    "💌 Яке послання я хочу передати собі на день?",
    "🔑 Яке ключове слово для мого сьогоднішнього дня?",
    "🛡️ Як я можу себе підтримати, якщо стане важко?",
    "🧭 Який внутрішній компас веде мене сьогодні?",
    "🌞 У чому я можу проявити себе справжньо сьогодні?",
    "🪄 Яке маленьке диво я готова/готовий помітити сьогодні?",
    "💭 Яка думка зараз звучить найгучніше?",
    "🧶 Що хоче розплутатись всередині мене сьогодні?",
    "🌱 Яке нове зернятко я можу посадити в собі сьогодні?",
    "✨ Яку чарівну дію я можу зробити сьогодні для себе або світу?"
] # сюди повний список
EVENING_QUESTIONS = [
    "🌙 Як пройшов мій день?",
    "🛏️ Який момент дня був для мене найтеплішим?",
    "🌟 Що сьогодні подарувало мені усмішку?",
    "💤 Що втомило мене сьогодні найбільше?",
    "🕯️ Що я сьогодні усвідомила/усвідомив?",
    "📘 Чого я навчилась/навчився сьогодні?",
    "❤️ Що сьогодні потішило моє серце?",
    "💧 Чи було щось, що зачепило або засмутило?",
    "🌈 Що я можу відпустити перед сном?",
    "🎁 Який внутрішній подарунок я отримала/отримав сьогодні?",
    "✨ Що сьогоднішній день додав до мого життя?",
    "🔮 Чи відчувала/відчував я синхронність або знак?",
    "🌌 Як я зараз почуваюся фізично?",
    "🧠 Яка думка не хоче залишити мене перед сном?",
    "💭 Про що я думаю перед тим, як заснути?",
    "🪞 Як я бачила/бачив себе сьогодні?",
    "🧡 Як я сьогодні проявила/проявив любов до себе?",
    "🌒 Чи було щось, що я не встигла/не встиг зробити — і як з цим зараз?",
    "🫧 Яке бажання з’явилося ввечері?",
    "🎈 Чи хочу я подякувати собі за щось сьогодні?",
    "🌠 Яка подія дня здається найважливішою?",
    "🔍 Що я помітила/помітив у своєму внутрішньому світі?",
    "📿 Яку практику я зробила/зробив для себе сьогодні?",
    "💌 Яке послання я б хотіла/хотів залишити собі на ніч?",
    "🌙 Як я можу обійняти себе зараз?",
    "🌊 Який настрій вечора?",
    "📖 Чи хочу я щось записати, щоб відпустити це з думок?",
    "🪷 Що я можу взяти з цього дня в майбутнє?",
    "🕊️ Який внутрішній стан я хочу перенести в сон?",
    "⭐ Який підсумок мого дня в одному слові або образі?"
]

# Карти
CARDS = [
    {"number": 1, "name": "Порожній простір", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/porojnijprostir.jpg"},
    {"number": 2, "name": "На роздоріжжі", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/narozdorijji.jpg"},
    {"number": 3, "name": "Запитання до неба", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/zapytannyadoneba.jpg"},
    {"number": 4, "name": "Дзеркало Всесвіту", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/dzerkalovsvesvitu.jpg"},
    {"number": 5, "name": "Порожня книга", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/porojnakniga.jpg"},
    {"number": 6, "name": "Тінь, що говорить", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/tishogovorit.jpg"},
    {"number": 7, "name": "Легкий вітерець", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/legkiyviterets.jpg"},
    {"number": 8, "name": "Стежка світла", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/steckasvitla.jpg"},
    {"number": 9, "name": "Дотик до невидимого", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/dotikdonevudumogo.jpg"},
    {"number": 10, "name": "Голос відлуння", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidlunnagolosu.jpg"},
    {"number": 11, "name": "Незнайоме обличчя", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/neznajomeoblicha.jpg"},
    {"number": 12, "name": "Двері, яких не було", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/dveryakihnebulo.jpg"},
    {"number": 13, "name": "Ключ без замка", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/kluchbezzamka.jpg"},
    {"number": 14, "name": "Сліди невидимого", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/slidichasu.jpg"},
    {"number": 15, "name": "Тіні у тумані", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/tiniytumani.jpg"},
    {"number": 16, "name": "Послання хвиль", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/poslannahvil.jpg"},
    {"number": 17, "name": "Несподіване тепло", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/nespodivaneteplo.jpg"},
    {"number": 18, "name": "Забутий спогад", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/zabutyispogad.jpg"},
    {"number": 19, "name": "Невідомий знак", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/nevidomijznak.jpg"},
    {"number": 20, "name": "Зупинений час", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/zupynenichas.jpg"},
    {"number": 21, "name": "Внутрішній вогонь", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vnutrishniyvogon.jpg"},
    {"number": 22, "name": "Оживлення", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/ogivlenna.jpg"},
    {"number": 23, "name": "Дозвіл летіти", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/dozvilzletity.jpg"},
    {"number": 24, "name": "Мить перед першим звуком", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/mitperedpershimzvukom.jpg"},
    {"number": 25, "name": "Танення реальності", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/tanennarealnosty.jpg"},
    {"number": 26, "name": "Розпад ілюзій", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/rozpadilyziy.jpg"},
    {"number": 27, "name": "Пастка можливостей", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/pastkamojlivostey.jpg"},
    {"number": 28, "name": "Послання всесвіту", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/poslannavsesvity.jpg"},
    {"number": 29, "name": "Скляна стіна", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/sklanastina.jpg"},
    {"number": 30, "name": "Відкриття сенсу", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidkryttasensu.jpg"},
    {"number": 31, "name": "Магія у звичайному", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/magiyauzvichainomu.jpg"},
    {"number": 32, "name": "Вага неможливого", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vaganemojlivogo.jpg"},
    {"number": 33, "name": "Крапля усвідомлення", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/krapliausvidomlenna.jpg"},
    {"number": 34, "name": "Перекручений світ", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/perrkruchenijsvit.jpg"},
    {"number": 35, "name": "Ехо знаків", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/ehoznakiv.jpg"},
    {"number": 36, "name": "Сліди руйнування", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/sludiruunuvanna.jpg"},
    {"number": 37, "name": "Музика, що лунає всередині", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/muzykasholunaevseredini.jpg"},
    {"number": 38, "name": "Примарний відбиток", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/prymarnyvidbitok.jpg"},
    {"number": 39, "name": "Розірваний ритм", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/rozirvaniyrytm.jpg"},
    {"number": 40, "name": "Тонка межа між снами", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/mejamijsnamu.jpg"},
    {"number": 41, "name": "Ледь відчутна зміна", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/ledpomitnizminy.jpg"},
    {"number": 42, "name": "Незавершена історія", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/nezavershenaistoriya.jpg"},
    {"number": 43, "name": "Пропущені шляхи", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/propyshenishlahi.jpg"},
    {"number": 44, "name": "Мінлива дорога", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/minlivadoroga.jpg"},
    {"number": 45, "name": "Сліди часу", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/slidichasu.jpg"},
    {"number": 46, "name": "Момент змін", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/perelomnamit.jpg"},
    {"number": 47, "name": "Глибока тиша", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/glibikatisha.jpg"},
    {"number": 48, "name": "Осяяння", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/osayanna.jpg"},
    {"number": 49, "name": "Відкриття істини", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidobragennaistini.jpg"},
    {"number": 50, "name": "Дотик землі", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/dotikzemli.jpg"},
    {"number": 51, "name": "Момент гармонії", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/momentgarmonii.jpg"},
    {"number": 52, "name": "У ритмі води", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/uritmivodi.jpg"},
    {"number": 53, "name": "Спокій у довірі", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/spokiyudoviri.jpg"},
    {"number": 54, "name": "Голос серця", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/golosserca.jpg"},
    {"number": 55, "name": "Єдність", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/ednist.jpg"},
    {"number": 56, "name": "Внутрішній напрямок", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vnutrishniynapramok.jpg"},
    {"number": 57, "name": "Вибух натхнення", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vibuhnathnenna.jpg"},
    {"number": 58, "name": "За межами горизонту", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/zamejamugorizontu.jpg"},
    {"number": 59, "name": "Пульсація всесвіту", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/pulsaciyavsvesvitu.jpg"},
    {"number": 60, "name": "Відкриті двері", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidkritidveri.jpg"},
    {"number": 61, "name": "Відображення істини", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidobragennaistini.jpg"},
    {"number": 62, "name": "Потік свободи", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/potiksvobodi.jpg"},
    {"number": 63, "name": "Резонанс із всесвітом", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/rezonanszvsesvitom.jpg"},
    {"number": 64, "name": "Відлуння натхнення", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/vidlunnagolosu.jpg"},
    {"number": 65, "name": "Легка хода долі", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/legkahodadoli.jpg"},
    {"number": 66, "name": "Тепло у дощі", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/teploudoshi.jpg"},
    {"number": 67, "name": "Око шторму", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/okoshtormu.jpg"},
    {"number": 68, "name": "Присутність у моменті", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/prisutnistymomenti.jpg"},
    {"number": 69, "name": "Подих свободи", "image_url": "https://raw.githubusercontent.com/Alona2503/Pdf_bot/main/images/duhannavoli.jpg"}
]
def get_user_file(user_id):
    return os.path.join(DATA_FOLDER, f"{user_id}.json")
def load_user_data(user_id):
    file_path = get_user_file(user_id)
    if not os.path.exists(file_path):
        data = {
            "name": "",
            "title": "",
            "entries": [],
            "used_morning": [],
            "used_evening": [],
            "card_date": "",
            "card_info": {}
        }
        save_user_data(user_id, data)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def save_user_data(user_id, data):
    file_path = get_user_file(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_entry(user_id, entry_type, content):
    data = load_user_data(user_id)
    data["entries"].append({
        "type": entry_type,
        "content": content,
        "timestamp": datetime.now(pytz.timezone("Europe/Kyiv")).isoformat()
    })
    save_user_data(user_id, data)
def start(update: Update, context: CallbackContext):
    welcome_message = (
        "🌿 Вітаю тебе у просторі Щоденника Інтуїції!\n"
        "— місці, де народжується чуття, глибина й внутрішній спокій.\n\n"
        "🪄 Цей щоденник створений, щоби підтримати тебе на шляху до себе.\n"
        "Тут не потрібно бути ідеальною — лише чесною з собою, ніжною, уважною.\n\n"
        "✨ Щоранку і щовечора ти зможеш чути себе краще: помічати настрій, фіксувати думки,\n"
        "ловити натхнення й звертати увагу на свої справжні бажання.\n\n"
        "🃏 Особливе місце займають метафоричні карти — вони мовчазні друзі, які не дають порад,\n"
        "а натякають образами. Вони допомагають побачити те, що вже є в тобі, але залишалось без уваги.\n\n"
        "📓 Цей щоденник — простір твого внутрішнього світу. Місце, де можна говорити щиро.\n"
        "Де твої слова мають значення. Де немає правильного чи неправильного.\n\n"
        "❤️ Тут важливе лише одне — ти.\n\n"
        "📌 А ще — як до тебе звертатися в цьому просторі?\n"
        "Напиши своє ім’я або псевдонім, яким ти хочеш підписати цей щоденник:"
    )
    update.message.reply_text(welcome_message)
    context.user_data["state"] = "waiting_name"

def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)
    text = update.message.text
    state = context.user_data.get("state")

    if state == "waiting_name":
        data["name"] = text
        save_user_data(user_id, data)
        name_reply = (
        "✨ Чудово!\n"
        "А тепер давай придумаємо назву для твого щоденника.\n"
        "Це може бути ніжне слово, метафора, фраза або просто щось, що відкликається саме зараз.\n\n"
        "Наприклад: «Шепіт серця», «Мій простір», «Світло всередині», «Подорож до себе»…\n\n"
        "🖋️ Напиши назву, яка стане підписом на обкладинці твого щоденника:"
    )
        update.message.reply_text(name_reply)
        context.user_data["state"] = "waiting_title"
    elif state == "waiting_title":
        data["title"] = text
        save_user_data(user_id, data)
        context.user_data["state"] = None

        final_text = (
        f"📓 Готово! Твій щоденник «{data['title']}» створено.\n\n"
        "🌟 Тепер ти можеш вирушити у мандрівку до себе — через слова, образи, відчуття.\n"
        "Довіряй кожному кроку і не поспішай: усе, що потрібно — вже всередині тебе.\n\n"
        "🧭 Використовуй /help, щоб дізнатися, з чого почати та які є команди для роботи з щоденником."
    )
    update.message.reply_text(final_text)
    
def reset_profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    filename = f"data/user_{user_id}.json"

    if os.path.exists(filename):
        os.remove(filename)
        update.message.reply_text("⚠️ Профіль повністю очищено. Надішліть своє ім’я для нового початку:")
        context.user_data.clear()
    else:
        update.message.reply_text("Профіль ще не створено.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📖 *Доступні команди Щоденника Інтуїції:*\n\n"
        "🃏 */card* — витягни карту дня. Вона допоможе краще налаштуватися на день, відчути напрям або натхнення.\n\n"
        "🌅 */morning* — відповіді на ранкові питання. Допомагають налаштуватися на день, почути себе та усвідомити свій стан.\n\n"
        "🌙 */evening* — вечірня рефлексія. Запитання, які допомагають завершити день з любов’ю до себе, зробити підсумок і відпустити зайве.\n\n"
        "📝 */note* — додай нотатку або фото. Можеш зберегти будь-які думки, фрагменти натхнення або кадри свого дня.\n\n"
        "📄 */mydairy* — створити PDF-файл твого щоденника. Він буде містити твої записи, карти, відповіді та фото, оформлені з титульною сторінкою.\n\n"
        "🔄 */resetprofile* — скинути ім’я та назву щоденника. Якщо хочеш змінити підпис або почати з нуля — скористайся цією командою.\n\n"
        "🧘 */maditation* — медитації. У майбутньому тут буде простір для заспокоєння, дихальних практик і повернення до себе.\n\n"
        "🧹 */cleardairy* — очистити щоденник. Залишається лише титульна сторінка — зручно для нового початку.\n\n"
        "🌟 Бот зберігає все, що ти вводиш протягом дня, і допомагає тобі створити особливий простір для себе.\n"
        "Пиши, відчувай, слухай себе — і твій Щоденник Інтуїції стане твоїм супутником."
    , parse_mode='Markdown')
import random

def card(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)
    today = datetime.now().date().isoformat()

    if data.get("card_date") == today:
        save_user_data(user_id, data)
        update.message.reply_text("🔮 Ти вже витягнула карту дня. Наступну можна буде завтра.")
        return

    card = random.choice(CARDS)

    # ВСТАВКА ТУТ
    filename = os.path.join(DATA_FOLDER, os.path.basename(card['image_url']))
    download_image(card["image_url"], filename)

    context.user_data["last_card"] = {
        "number": card["number"],
        "name": card["name"],
        "image_path": filename
    }

    context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=open(filename, "rb"),
        caption=f"📍 Карта дня\nНомер: {card['number']}\nНазва: {card['name']}"
    )
    kyiv_time = datetime.now(pytz.timezone("Europe/Kyiv"))

    data["entries"].append({
        "type": "card_response",
        "content": {
            "number": card["number"],
            "name": card["name"],
            "image": filename,
            "text": ""  # якщо немає відповіді користувача
        },
        "timestamp": kyiv_time.isoformat()
    })
    data["card_date"] = today
    data["card_info"] = card
    save_user_data(user_id, data)
    update.message.reply_text("✍️ Напиши свої інсайти щодо карти:")
    context.user_data["state"] = "card_response"

def morning(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)

    available = list(set(MORNING_QUESTIONS) - set(data["used_morning"]))
    if not available:
        update.message.reply_text("🌞 Ти відповіла на всі ранкові питання.\n/cleardairy — щоб почати новий цикл.")
        return

    question = random.choice(available)
    data["used_morning"].append(question)
    save_user_data(user_id, data)

    update.message.reply_text(f"☀️ {question}")
    context.user_data["state"] = "morning_response"
    question = random.choice(available)
    kyiv_time = datetime.now(pytz.timezone("Europe/Kyiv"))

    data["entries"].append({
        "type": "morning",
        "question": question,
        "content": "",
        "timestamp": kyiv_time.isoformat()
    })
    save_user_data(user_id, data)
    context.user_data["current_question"] = question
    
def evening(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)

    available = list(set(EVENING_QUESTIONS) - set(data["used_evening"]))
    if not available:
        update.message.reply_text("🌙 Всі вечірні питання використані. /cleardairy — щоб почати знову.")
        return

    question = random.choice(available)
    data["used_evening"].append(question)
    save_user_data(user_id, data)

    context.user_data["current_question"] = question
    update.message.reply_text(f"🌙 {question}")
    context.user_data["state"] = "evening_response"
    kyiv_time = datetime.now(pytz.timezone("Europe/Kyiv"))

    data["entries"].append({
        "type": "evening",
        "question": question,
        "content": "",
        "timestamp": kyiv_time.isoformat()
    })
    save_user_data(user_id, data)
from telegram import InputMediaPhoto
from telegram.ext import MessageHandler, Filters
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
from textwrap import wrap

def note(update: Update, context: CallbackContext):
    update.message.reply_text("✍️ Надішли текст або фото — я збережу це у щоденнику.")
    context.user_data["state"] = "note_entry"

def save_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1].get_file()
    img_path = os.path.join(DATA_FOLDER, f"{user_id}_{photo.file_id}.jpg")
    photo.download(img_path)
    add_entry(user_id, "image", img_path)
    update.message.reply_text("📸 Фото збережено!")

def maditation(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("🧘 Спокій"), KeyboardButton("✨ Відновлення")],
        [KeyboardButton("🔥 Натхнення"), KeyboardButton("🌊 Потік")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("🧘 Обери медитацію (незабаром будуть активні):", reply_markup=reply_markup)

def cleardairy(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)
    title = data["title"]
    name = data["name"]

    # очищаємо все крім титулки
    new_data = {
        "name": name,
        "title": title,
        "entries": [],
        "used_morning": [],
        "used_evening": [],
        "card_date": "",
        "card_info": {}
    }
    save_user_data(user_id, new_data)
    update.message.reply_text("🗑 Щоденник очищено (титульна сторінка збережена).")
def check_space(canvas, y, required_height, bg, width, height, margin):
    if y - required_height < margin:
        canvas.showPage()
        canvas.drawImage(bg, 0, 0, width=width, height=height)
        return height - margin  # новий y після переходу
    return y  # залишає поточний y 
import textwrap

def estimate_text_height(text, max_width_chars=90, font_size=14, line_spacing=2):
    """
    Оцінює висоту тексту в пікселях для перевірки, чи вміститься він на сторінці.
    Параметр max_width_chars — це скільки символів у рядок при поточному шрифті.
    """
    paragraphs = text.split("\n")
    total_lines = 0
    for paragraph in paragraphs:
        wrapped = textwrap.wrap(paragraph, width=max_width_chars)
        total_lines += len(wrapped) + 1  # +1 — це відступ між абзацами
    line_height = font_size + line_spacing
    return total_lines * line_height
def draw_wrapped_text(canvas, text, x, y, max_width, line_height, font_name="DejaVu", font_size=14):
    canvas.setFont(font_name, font_size)
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if canvas.stringWidth(test_line, font_name, font_size) < max_width:
            line = test_line
        else:
            canvas.drawString(x, y, line.strip())
            y -= line_height
            line = word + " "
    if line:
        canvas.drawString(x, y, line.strip())
        y -= line_height
    return y  # повертаємо нову координату
def mydairy(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    data = load_user_data(user_id)  # Правильне завантаження
    pdf_path = os.path.join(PDF_FOLDER, f"dairy_{user_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 50
    max_width = width - 2 * margin

    pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))

    # титульна сторінка
    bg = ImageReader(BACKGROUND_IMAGE)
    c.drawImage(bg, 0, 0, width, height)
    c.setFont("DejaVu", 30)
    c.drawCentredString(width / 2, height - 100, data["title"])
    c.setFont("DejaVu", 20)
    c.drawCentredString(width / 2, height - 140, f"Автор: {data['name']}")
    c.setFont("DejaVu", 16)
    c.drawCentredString(width / 2, height - 180, f"Дата: {datetime.now().strftime('%Y-%m-%d')}")
    c.showPage()

    # вміст
    y = height - margin
    c.drawImage(bg, 0, 0, width, height)
    c.setFont("DejaVu", 16)

    for entry in data["entries"]:
        if entry["type"] == "note":
            # перевірити чи є місце перед вставкою нового блоку
            if y < 150:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                y = height - margin
            timestamp = format_datetime_ukr(datetime.fromisoformat(entry["timestamp"]))
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, f"{timestamp}")
            y -= 24

            c.setFont("DejaVu", 16)
            c.drawString(margin, y, "✏️ Нотатка:")
            y -= 24

            lines = entry["content"]
            full_text = text
            required_height = estimate_text_height(full_text)
            y = check_space(c, y, required_height, bg, width, height, margin)
            y = draw_wrapped_text(c, full_text, margin, y, max_width=500, line_height=20)
            y -= 10

            if y < 100:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                c.setFont("DejaVu", 14)
                y = height - margin

            draw_wrapped_text(
                c, full_text,
                x=margin,
                y=y,
                max_width=width - 2 * margin,
                font_size=14,
                line_height=20
            )

            lines_count = len(full_text) // 70 + full_text.count("\n")
            y -= lines_count * 18 + 10

        elif entry["type"] == "image":
            if os.path.exists(entry["content"]):
                timestamp = format_datetime_ukr(datetime.fromisoformat(entry["timestamp"]))
                c.setFont("DejaVu", 14)
                c.drawString(margin, y, f"{timestamp}")
                y -= 24
                img = Image.open(entry["content"])
                img.thumbnail((400, 400))
                img_width, img_height = img.size
                if y < img_height + 60:
                    c.showPage()
                    c.drawImage(bg, 0, 0, width, height)
                    y = height - margin
                x = (width - img_width) / 2
                c.drawImage(entry["content"], x, y - img_height, img_width, img_height)
                y -= img_height + 30

        elif entry["type"] == "card_response":
            # перевірити чи є місце перед вставкою нового блоку
            if y < 150:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                y = height - margin
            timestamp = format_datetime_ukr(datetime.fromisoformat(entry["timestamp"]))
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, f"{timestamp}")
            y -= 24
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, "🔮 Інсайт до карти дня:")
            y -= 24

            if "image" in entry["content"] and os.path.exists(entry["content"]["image"]):
                img = Image.open(entry["content"]["image"])
                img.thumbnail((400, 400))
                img_width, img_height = img.size
                if y < img_height + 60:
                    c.showPage()
                    c.drawImage(bg, 0, 0, width, height)
                    y = height - margin
                x = (width - img_width) / 2
                c.drawImage(entry["content"]["image"], x, y - img_height, img_width, img_height)
                y -= img_height + 30

            card_name = entry["content"].get("name", "")
            card_number = entry["content"].get("number", "")
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, f"Карта: {card_name} (№{card_number})")
            y -= 24

            full_text = f"Карта: {card_name} (№{card_number})\n\nІнсайт:\n{text}"
            required_height = estimate_text_height(full_text)
            y = check_space(c, y, required_height, bg, width, height, margin)
            y = draw_wrapped_text(c, full_text, margin, y, max_width=500, line_height=20)
            y -= 10
            if y < 100:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                c.setFont("DejaVu", 14)
                y = height - margin

            y = draw_wrapped_text(c, full_text, x=margin, y=y, max_width=500, line_height=20)
            y -= 10  # тільки додатковий відступ, якщо хочеш

        elif entry["type"] == "morning_answer":
            # перевірити чи є місце перед вставкою нового блоку
            if y < 150:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                y = height - margin
            timestamp = format_datetime_ukr(datetime.fromisoformat(entry["timestamp"]))
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, f"{timestamp}")
            y -= 24
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, "☀️ Ранкова відповідь:")
            y -= 24
            question = entry["content"].get("question", "")
            answer = entry["content"].get("text", "")
            full_text = f"{question}\n\nВідповідь:\n{answer}"
            required_height = estimate_text_height(full_text)
            y = check_space(c, y, required_height, bg, width, height, margin)
            y = draw_wrapped_text(c, full_text, margin, y, max_width=500, line_height=20)
            y -= 10
            if y < 100:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                c.setFont("DejaVu", 14)
                y = height - margin

            y = draw_wrapped_text(c, full_text, x=margin, y=y, max_width=500, line_height=20)
            y -= 10  # тільки додатковий відступ, якщо хочеш

        elif entry["type"] == "evening_answer":
            # перевірити чи є місце перед вставкою нового блоку
            if y < 150:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                y = height - margin
            timestamp = format_datetime_ukr(datetime.fromisoformat(entry["timestamp"]))
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, f"{timestamp}")
            y -= 24
            c.setFont("DejaVu", 14)
            c.drawString(margin, y, "🌙 Вечірня рефлексія:")
            y -= 24
            question = entry["content"].get("question", "")
            answer = entry["content"].get("text", "")
            full_text = f"{question}\n\nВідповідь:\n{answer}"
            required_height = estimate_text_height(full_text)
            y = check_space(c, y, required_height, bg, width, height, margin)
            y = draw_wrapped_text(c, full_text, margin, y, max_width=500, line_height=20)
            y -= 10
            if y < 100:
                c.showPage()
                c.drawImage(bg, 0, 0, width, height)
                c.setFont("DejaVu", 14)
                y = height - margin

            y = draw_wrapped_text(c, full_text, x=margin, y=y, max_width=500, line_height=20)
            y -= 10  # тільки додатковий відступ, якщо хочеш

    c.save()

    if os.path.exists(pdf_path):
        update.message.reply_document(
            document=open(pdf_path, "rb"),
            filename="Щоденник_Інтуїції.pdf"
        )
    else:
        update.message.reply_text("❌ Сталася помилка при створенні PDF.")
     
def handle_response(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    state = context.user_data.get("state")

    if state == "card_response":
        last_card = context.user_data.get("last_card")
        if last_card:
            data = load_user_data(user_id)
            for entry in reversed(data["entries"]):
                if entry["type"] == "card_response":
                    entry["content"]["text"] = text
                    break
            save_user_data(user_id, data)
            context.user_data["state"] = None
            update.message.reply_text("✅ Інсайт до карти збережено!")

    elif state == "morning_response":
        question = context.user_data.get("current_question", "")
        add_entry(user_id, "morning_answer", {
            "question": question,
            "text": text
        })
        context.user_data["state"] = None
        update.message.reply_text("✅ Ранкова відповідь збережена!")

    elif state == "evening_response":
        question = context.user_data.get("current_question", "")
        add_entry(user_id, "evening_answer", {
            "question": question,
            "text": text
        })
        context.user_data["state"] = None
        update.message.reply_text("✅ Вечірня відповідь збережена!")

    elif state == "note_entry":
            # Розбиваємо текст на рядки перед збереженням
        lines = text.split('\n')
        add_entry(user_id, "note", lines)
        context.user_data["state"] = None
        update.message.reply_text("✅ Нотатка збережена!")

    else:
        handle_text(update, context)

def main():
    TOKEN = "8117433230:AAEJ2OXuMBtca7bBi1SD0d9sbpp2osG-GSM"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("Card", card))
    dp.add_handler(CommandHandler("Morning", morning))
    dp.add_handler(CommandHandler("Evening", evening))
    dp.add_handler(CommandHandler("Note", note))
    dp.add_handler(CommandHandler("maditation", maditation))
    dp.add_handler(CommandHandler("Mydairy", mydairy))
    dp.add_handler(CommandHandler("Cleardairy", cleardairy))
    dp.add_handler(MessageHandler(Filters.photo, save_image))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_response))
    dp.add_handler(CommandHandler("resetprofile", reset_profile))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
