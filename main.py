from flask import Flask, request, Response
import os
import logging
from logging.handlers import RotatingFileHandler
import telebot
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =========================
# Flask + Telegram Webhook Bot
# =========================


app = Flask(__name__)

# --- logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger("telegram_bot")
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

stream_h = logging.StreamHandler()
stream_h.setLevel(LOG_LEVEL)
stream_h.setFormatter(formatter)
logger.addHandler(stream_h)

file_h = RotatingFileHandler(os.path.join(log_dir, "bot.log"), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_h.setLevel(LOG_LEVEL)
file_h.setFormatter(formatter)
logger.addHandler(file_h)

# =========================
# HELPER FUNCTIONS
# =========================
def convert_markdown_links_to_html(text):
    """Convert markdown-style links (text)[url] to HTML anchor tags <a href="url">text</a>"""
    pattern = r'\(([^\)]+)\)\[([^\]]+)\]'
    replacement = r'<a href="\2">\1</a>'
    return re.sub(pattern, replacement, text)

TOKEN = os.getenv("API_TOKEN", "none")
if (TOKEN == "none"):
    logger.error("API_TOKEN environment variable not set. Exiting.")
    exit(1)
bot = telebot.TeleBot(TOKEN)
DATA_PATH = "data"

# =========================
# MENUS
# =========================
menus = {
    "menu0":{
        "title": "ℹ️ تعرف علينا"
    },
    "menu1": {
        "title": "🏫 القبول والتسجيل",
        "items": [
            "📅 الخط الزمني للفصول",
            "🕐 مواعيد القبول والتسجيل للفصل القادم",
            "📝 التقديم اليدوي للكلية",
            "📖 أقسام الكلية",
            "🌙 الدبلوم المسائي",
            "📘 معادلة مقررات الكلية",
            "🏅 متفوقو الكلية",
        ],
    },
    "menu2": {
        "title": "🎓 شؤون المتدربين",
        "items": [
            "📋 الخطط التدريبية",
            "📧 بريد المتدرب الرسمي",
            "💰 المكافأة",
            "⚠️ آلية الاعتراض",
            "🚫 الحرمان وحالات الإنذار",
            "🚫 الحرمان وحالات الإنذار 1",
            "📗 دليل المتدرب",
            "💳 الشؤون المالية للمتدرب",
            "🧰 أدوات مساعدة للمتدرب",
            "📝 تقديم شكوى أو اعتراض من المتدرب",
            "🤲 خدمة المجتمع",
        ],
    },
    "menu3": {
        "title": "📚 الشؤون الأكاديمية",
        "items": [
            "🧮 إرشادات الاختبارات والتقييمات",
            "📖 دليل التصنيف",
            "📑 تقرير المقررات المتبقية",
            "📞 التواصل مع أقسام الكلية",
            "🤝 التدريب التعاوني",
            "🎓 برنامج دعم مشاريع التخرج",
            "🧭 مكتب التنسيق الوظيفي",
            "📝 إرشادات الاختبارات ولتقييمات2",
        ],
    },
    "menu4": {
        "title": "💻 المنصات والخدمات الإلكترونية",
        "items": [
            "🌐 منصة خدمات المتدربين ومنصة رايات",
            "💼 منصة المكتب Office 365 ومنصة البريد بيرود",
            "📲 التواصل مع رايات",
            "📘 معلومات مهمة للمستجدين والمستمرين",
            "🆕 معلومات مهمة للمستجدين",
            "🗓️ التقويم التدريبي",
        ],
    },
    "menu5": {
        "title": "🤝 التواصل والدعم",
        "items": [
            "📨 التواصل مع الكلية",
            "📞 التواصل مع أقسام الكلية",
            "🏅 متفوقو المؤسسة",
            "🚗 مواقف المتدربين داخل حرم الكلية",
        ],
    },
    "menu6": {
        "title": "🌍 الشهادات والأكاديميات",
        "items": [
            "🎓 الأكاديميات الدولية",
            "📜 الشهادات الاحترافية والأكاديميات الدولية",
        ],
    },
    "menu7": {
        "title": "🏠 الخدمات العامة والمساندة",
        "items": [
            "🏠 سكن الكلية",
            "📊 طريقة عرض الجدول في رايات",
            "📄 برشور قديم",
            "📄 1برشور قديم",
        ],
    },
}

# =========================
# command system
# (sections used ONLY for /cmd_N slash command list — same as bot.py2.py)
# message navigation still uses the menus dict above
# =========================
_sections_for_cmds = {
    "sec_a": {
        "items": [
            "📅 الخط الزمني للفصول",
            "🕐 مواعيد القبول والتسجيل للفصل القادم",
            "📝 التقديم اليدوي للكلية",
            "📖 أقسام الكلية",
            "🌙 الدبلوم المسائي",
            "📘 معادلة مقررات الكلية",
            "🏅 متفوقو الكلية",
            "🧮 إرشادات الاختبارات والتقييمات",
            "📖 دليل التصنيف",
            "📑 تقرير المقررات المتبقية",
            "🤝 التدريب التعاوني",
            "🎓 برنامج دعم مشاريع التخرج",
            "🧭 مكتب التنسيق الوظيفي",
            "📝 إرشادات الاختبارات ولتقييمات2",
        ],
    },
    "sec_b": {
        "items": [
            "📋 الخطط التدريبية",
            "📧 بريد المتدرب الرسمي",
            "💰 المكافأة",
            "⚠️ آلية الاعتراض",
            "🚫 الحرمان وحالات الإنذار",
            "🚫 الحرمان وحالات الإنذار 1",
            "📗 دليل المتدرب",
            "💳 الشؤون المالية للمتدرب",
            "🧰 أدوات مساعدة للمتدرب",
            "📝 تقديم شكوى أو اعتراض من المتدرب",
            "🤲 خدمة المجتمع",
            "🏅 متفوقو المؤسسة",
        ],
    },
    "sec_c": {
        "items": [
            "🌐 منصة خدمات المتدربين ومنصة رايات",
            "💼 منصة المكتب Office 365 ومنصة البريد بيرود",
            "📲 التواصل مع رايات",
            "📘 معلومات مهمة للمستجدين والمستمرين",
            "🆕 معلومات مهمة للمستجدين",
            "التقويم التدريبي",
            "📨 التواصل مع الكلية",
            "📞 التواصل مع أقسام الكلية",
            "🚗 مواقف المتدربين داخل حرم الكلية",
            "🎓 الأكاديميات الدولية",
            "📜 الشهادات الاحترافية والأكاديميات الدولية",
            "🏠 سكن الكلية",
            "📊 طريقة عرض الجدول في رايات",
            "📄 برشور قديم",
            "📄 1برشور قديم",
        ],
    },
}

INFO_ITEM = "ℹ️ تعرف علينا"
items_list = [INFO_ITEM]
_seen = {INFO_ITEM}
for _sec in _sections_for_cmds.values():
    for _it in _sec["items"]:
        if _it not in _seen:
            _seen.add(_it)
            items_list.append(_it)

# ===== إنشاء القائمة الرئيسية =====
def main_menu():
    # Reply keyboard with one button per row (fixed buttons)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    for key, menu in menus.items():
        markup.row(KeyboardButton(menu["title"]))
    return markup


def main_menu_inline():
    """Inline keyboard for the main menu so it can be shown inside the same message.
    We also set a reply keyboard separately (sent then deleted) to keep the reply keys visible.
    Callback format: menu|<menu_key>
    """
    markup = InlineKeyboardMarkup()
    for key, menu in menus.items():
        markup.add(InlineKeyboardButton(menu["title"], callback_data=f"menu|{key}"))
    return markup


# ===== إنشاء قائمة فرعية =====
def submenu(menu_key):
    """Create an inline submenu using stable short callback_data:
    callback format: item|<menu_key>|<index>
    This avoids long/truncated callback_data and keeps behavior consistent with submenu_inline.
    """
    markup = InlineKeyboardMarkup()
    if "items" in menus[menu_key]:
        for idx, item in enumerate(menus[menu_key]["items"]):
            cb = f"item|{menu_key}|{idx}"
            markup.add(InlineKeyboardButton(item, callback_data=cb))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return markup


def submenu_inline(menu_key):
    """Return an InlineKeyboardMarkup for the submenu so we can send it as a new message
    (keeps the reply keyboard visible). Uses short callback_data in the form: item|<menu_key>|<index>
    """
    markup = InlineKeyboardMarkup()
    if "items" in menus[menu_key]:
        for idx, item in enumerate(menus[menu_key]["items"]):
            cb = f"item|{menu_key}|{idx}"
            markup.add(InlineKeyboardButton(item, callback_data=cb))
    # add a close button to remove the inline menu message
    markup.add(InlineKeyboardButton("🔙 إغلاق", callback_data=f"close|{menu_key}"))
    return markup


# ===== /start =====
text = """
مرحباً بك انا مساعدك التقني 🤖 .. 

🌟 لمساعدة متدربي كليات الاتصالات 
دبلوم و بكالوريوس  بنين ..

🔻كل اللي عليك تضغط على الأزرار 
الي حاب تعرف أجابته ..



حساب (X) <a href='https://x.com/tcti_edu?s=21'>كلية الاتصالات  والمعلومات بجدة</a> 


حساب (X) <a href='https://x.com/tvtcweb?s=11'>التدريب التقني</a>
"""
@bot.message_handler(commands=["start"])
def start(message): 
    logger.info("/start from chat_id=%s user=%s", message.chat.id, getattr(message.from_user, 'id', None))
    # send the visible menu as an inline keyboard (so the message contains the buttons)
    bot.send_message(message.chat.id, text, reply_markup=main_menu_inline(), parse_mode="HTML")

    # then send a short message with the ReplyKeyboardMarkup to set the reply keyboard for the chat
    # and delete that helper message so the user only sees the inline-menu message.
    try:
        # send a helper message which sets the ReplyKeyboardMarkup for the chat.
        # NOTE: do NOT delete this helper message — deleting it can remove the reply keyboard in some clients.
        helper = bot.send_message(
            message.chat.id,
            "سوف تجد ازرار الوصول للمحتوى متاحه في القائمة اسفل الشاشة للوصول بشكل أسرع.",
            reply_markup=main_menu(),
        )
        logger.info("sent helper message id=%s to set reply keyboard for chat_id=%s", getattr(helper, 'message_id', None), message.chat.id)
    except Exception as e:
        # if setting the reply keyboard fails, ignore — the inline menu still works
        logger.exception("failed to set reply keyboard for chat_id=%s: %s", message.chat.id, e)

# ===== التعامل مع أوامر /cmd_N =====
@bot.message_handler(regexp=r"^/cmd_\d+(@\w+)?$")
def handle_cmd_slash(message):
    raw = message.text.split("@", 1)[0]  # strip @botname suffix
    try:
        idx = int(raw.replace("/cmd_", ""))
        item_name = items_list[idx]
    except Exception:
        bot.send_message(message.chat.id, "أمر غير معروف")
        return
    logger.info("slash command -> item '%s'", item_name)
    send_folder_content(message.chat.id, item_name)


# ===== التعامل مع الضغط على الأزرار =====
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    logger.info("message from chat_id=%s: %s", message.chat.id, text)

    # map menu titles to keys
    title_to_key = {menu["title"]: key for key, menu in menus.items()}

    # If user pressed a main menu button, send the submenu as a NEW message with inline buttons
    # this keeps the main reply keyboard visible while the submenu appears as an inline keyboard
    if text in title_to_key:
        key = title_to_key[text]
        if "items" not in menus[key]:
            # no submenu, send folder content directly
            logger.info("sending folder content for menu_key=%s", key)
            send_folder_content(message.chat.id, menus[key]["title"])
            return
        bot.send_message(message.chat.id, menus[key]["title"], reply_markup=submenu_inline(key))
        return

    # Back to main menu
    if text == "🔙 رجوع":
        bot.send_message(message.chat.id, "👋 مرحباً بك!\nاختر من التصنيفات التالية:", reply_markup=main_menu())
        logger.info("sent main menu reply keyboard to chat_id=%s", message.chat.id)
        return

    # If pressed an item button, send folder content
    for key, menu in menus.items():
        if text in menu["items"]:
            logger.info("selected item '%s' from menu '%s'", text, key)
            send_folder_content(message.chat.id, text)
            return

    # Unknown input: ignore or inform user
    # (optional) send a help message or re-show main menu
    # bot.send_message(message.chat.id, "اختر أحد الأزرار أدناه:", reply_markup=main_menu())


# ===== إرسال محتوى المجلد =====
def send_folder_content(chat_id, item_name):
    logger.info("send_folder_content: chat_id=%s item=%s", chat_id, item_name)
    folder_path = os.path.join(DATA_PATH, item_name)
    if not os.path.exists(folder_path):
        logger.warning("folder not found: %s", folder_path)
        bot.send_message(chat_id, f"❌ لا يوجد محتوى في القسم {item_name}")
        return

    files = os.listdir(folder_path)
    if not files:
        bot.send_message(chat_id, f"📂 قسم {item_name} فارغ حالياً.")
        return

    for file in files:
        path = os.path.join(folder_path, file)

        if file.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    text_content = f.read().strip()
                    text_content = convert_markdown_links_to_html(text_content)
                    bot.send_message(chat_id, text_content, parse_mode="HTML")
                except Exception as e:
                    logger.exception("failed to send text file %s to chat_id=%s: %s", path, chat_id, e)

        elif file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            with open(path, "rb") as img:
                try:
                    bot.send_photo(chat_id, img)
                except Exception as e:
                    logger.exception("failed to send image %s to chat_id=%s: %s", path, chat_id, e)

        else:
            with open(path, "rb") as doc:
                try:
                    bot.send_document(chat_id, InputFile(doc, file_name=file))
                except Exception as e:
                    logger.exception("failed to send document %s to chat_id=%s: %s", path, chat_id, e)



# ===== التعامل مع الضغط على أزرار القوائم الداخلية (Inline) =====
@bot.callback_query_handler(func=lambda call: True)
def inline_callback(call):
    data = call.data or ""

    if data.startswith("item|"):
        # format: item|<menu_key>|<index>
        parts = data.split("|")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return
        _, menu_key, idx = parts
        try:
            idx = int(idx)
            item_name = menus[menu_key]["items"][idx]
        except Exception:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return

        # send the folder content for the selected item
        send_folder_content(call.message.chat.id, item_name)
        bot.answer_callback_query(call.id)
    elif data.startswith("menu|"):
        # format: menu|<menu_key>
        parts = data.split("|")
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return
        _, menu_key = parts
        if menu_key not in menus:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر")
            return

        if "items" not in menus[menu_key]:
            # no submenu, send folder content directly
            send_folder_content(call.message.chat.id, menus[menu_key]["title"])
            bot.answer_callback_query(call.id)
            return
        
        # edit message to show submenu
        bot.edit_message_text(
            menus[menu_key]["title"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=submenu(menu_key),
        )

        bot.answer_callback_query(call.id)
    elif data == "back_main":
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu_inline(),
            parse_mode="HTML"
            
        )
        bot.answer_callback_query(call.id)
    elif data.startswith("close|"):
        # remove the inline menu message (if possible)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            # ignore delete failures
            pass
        bot.answer_callback_query(call.id)


# =========================
# FLASK ROUTES
# =========================
@app.route('/logs')
def logs_route():
    log_file = os.path.join(log_dir, 'bot.log')
    if not os.path.exists(log_file):
        return Response('Log file not found', mimetype='text/plain')
    with open(log_file, 'r', encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/plain')

@app.route("/")
def home():
    return "Bot is running."

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_data = request.get_json(force=True)
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

# =========================
# START WEBHOOK
# =========================

if __name__ == "__main__":
    import requests

    # For local development with ngrok:
    # 1. Install: pip install pyngrok
    # 2. Run: ngrok http 5000
    # 3. Copy the URL and set WEBHOOK_URL below
    
    # WEBHOOK_URL = "https://your-ngrok-url.ngrok.io/" + TOKEN  # Replace with your ngrok URL
    
    # Or use your public Render URL for production:
    WEBHOOK_URL = "https://telegram-bot-1-gjjw.onrender.com/" + TOKEN
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    except Exception as e:
        print("Failed to set webhook:", e)

    # Register /cmd_N slash commands with Telegram (appears in the / menu)
    try:
        cmds = [telebot.types.BotCommand(f"cmd_{idx}", item[:256])
                for idx, item in enumerate(items_list)][:100]
        scopes = [
            None,
            telebot.types.BotCommandScopeDefault(),
            telebot.types.BotCommandScopeAllPrivateChats(),
            telebot.types.BotCommandScopeAllGroupChats(),
            telebot.types.BotCommandScopeAllChatAdministrators(),
        ]
        for sc in scopes:
            try:
                if sc is None:
                    bot.set_my_commands(cmds)
                else:
                    bot.set_my_commands(cmds, scope=sc)
            except Exception as e:
                print(f"set_my_commands failed for scope {sc}: {e}")
        print(f"Registered {len(cmds)} slash commands across all scopes.")
    except Exception as e:
        print("Failed to register commands:", e)

    app.run(host="0.0.0.0", port=5000)
