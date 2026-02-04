from typing import Final
import sqlite3
from pathlib import Path

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============================
# CONFIG
# ============================

TOKEN: Final = "8543113287:AAFjKFGXULDtlZwj_UK8leN3rr5f4DzXlcc"
BOT_USERNAME: Final = "@popobot_popo_bot"
ADMIN_CHAT_ID: Final = 6714153411  # ← put your Telegram user ID here
DB_PATH = Path("coop_requests.db")

PAGE_SIZE = 10  # items per page in perfume lists


# ============================
# DB SETUP
# ============================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS coop_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            request_type TEXT,
            full_name TEXT,
            phone TEXT,
            link TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_coop_request(user_id, username, data: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO coop_requests (user_id, username, request_type, full_name, phone, link)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            data.get("request_type"),
            data.get("full_name"),
            data.get("phone"),
            data.get("link"),
        ),
    )
    conn.commit()
    conn.close()


# ============================
# DATA
# ============================

perfume_lists = {
    "women": [
        "باربری هر", "بیلی آیلیش", "جورجیو ارمانی استرانگر", "لیبر",
        "کایالی مارشمالو", "یارا صورتی", "یارا کندی", "بامبشل ویکتوریا",
        "لاگوست پینک", "جنیفر لوپز استیل", "لویی ویلتون میل فو",
        "د مارلی والایا", "تیلور سوییف واندر", "باربری گادرس", "لوی بل",
        "کریکه", "کویین آو سیلک", "باکارات رژ", "مارلی کارایل", "نارسیسو",
        "گرند اری", "ارباپورا", "امواج هانر", "لاتوسکا", "ایفوریا",
        "اسکندل", "گودگرل", "گابلنا کویین", "مارلی کسیلی", "هالویین",
        "لامور", "المپیا", "گرن بالو", "اکلت", "جیوانجی لسکرت",
    ],
    "men": [
        "فارنهایت دیور", "جورجیو استرانگر", "مارلی کارایل", "اپن",
        "توسکان", "پلاتینیوم", "رورینگ", "اومو ولنتینو", "اینترلود امواج",
        "سدراطلس", "ژاوی", "هیرود مارلی", "فبیولس", "پورهوم", "بلوشنل",
        "دنجر رژا", "دیزایربلو", "سی اچ", "اونتوس", "کرید وایکینگ",
        "اروس", "کالان", "۲۱۲", "اکسنتو", "گری وتیور", "موروکن لدر",
        "نارسیسو",
    ],
    "unisex": ["1"],
}


# ============================
# MENUS
# ============================

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["محصولات 🛍️"],
            ["راهنما 📖", "درباره ما 🧾"],
            ["درخواست همکاری 🤝"],
        ],
        resize_keyboard=True,
    )


def product_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("۱- عطر", callback_data="product_perfume")],
        [InlineKeyboardButton("۲- کرم", callback_data="product_cream")],
        [InlineKeyboardButton("۳- بادی اسپلش", callback_data="product_body")],
        [InlineKeyboardButton("۴- اسپری", callback_data="product_spray")],
    ])


def gender_menu(prefix: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("زنانه 🌸", callback_data=f"{prefix}_women_page_0")],
        [InlineKeyboardButton("مردانه 🕴️", callback_data=f"{prefix}_men_page_0")],
        [InlineKeyboardButton("یونیسکس 🤍", callback_data=f"{prefix}_unisex_page_0")],
        [InlineKeyboardButton("بازگشت 🔙", callback_data="back_to_products")],
    ])


def perfume_page_keyboard(kind: str, gender: str, page: int, total_pages: int):
    buttons = []

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton("⬅️ قبلی", callback_data=f"{kind}_{gender}_page_{page-1}")
        )
    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton("بعدی ➡️", callback_data=f"{kind}_{gender}_page_{page+1}")
        )
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("بازگشت 🔙", callback_data=f"back_to_gender_{kind}")
    ])

    return InlineKeyboardMarkup(buttons)


# ============================
# COMMANDS
# ============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام، خوش آمدید. یکی از گزینه‌ها رو انتخاب کنید:",
        reply_markup=main_menu_keyboard(),
    )


# ============================
# CALLBACK HANDLER
# ============================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Back buttons
    if data == "back_to_products":
        return await query.message.reply_text(
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=product_menu(),
        )

    if data == "back_to_gender_perfume":
        return await query.message.reply_text(
            "نوع عطر را انتخاب کنید:",
            reply_markup=gender_menu("perfume"),
        )

    # Product → Gender
    if data == "product_perfume":
        return await query.message.reply_text(
            "نوع عطر را انتخاب کنید:",
            reply_markup=gender_menu("perfume"),
        )

    # Cooperation form start
    if data == "send_coop_request":
        context.user_data["coop_state"] = 1
        context.user_data["coop_data"] = {}
        return await query.message.reply_text("1️⃣ نوع درخواست را بنویسید:")

    # Perfume pagination: perfume_<gender>_page_<n>
    if data.startswith("perfume_") and "_page_" in data:
        _, gender, _, page_str = data.split("_")
        page = int(page_str)
        items = perfume_lists.get(gender, [])
        total_pages = (len(items) + PAGE_SIZE - 1) // PAGE_SIZE or 1

        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = items[start:end]

        text = "\n".join(f"• {item}" for item in page_items) or "موردی یافت نشد."
        text = f"لیست عطرهای {gender} (صفحه {page+1} از {total_pages}):\n\n" + text

        return await query.message.reply_text(
            text,
            reply_markup=perfume_page_keyboard("perfume", gender, page, total_pages),
        )


# ============================
# COOP FORM (STEP-BY-STEP)
# ============================

async def handle_coop_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("coop_state")
    data = context.user_data.get("coop_data", {})
    text = update.message.text.strip()

    if state == 1:
        data["request_type"] = text
        context.user_data["coop_state"] = 2
        return await update.message.reply_text("2️⃣ نام و نام خانوادگی را بنویسید:")

    if state == 3:
        # Validate phone number
        if not text.isdigit():
            return await update.message.reply_text("❌ لطفاً فقط عدد وارد کنید.\nمثال: 09123456789")

        if len(text) < 11:
            return await update.message.reply_text("❌ شماره تماس باید حداقل ۱۱ رقم باشد.\nمثال: 09123456789")

        data["phone"] = text
        context.user_data["coop_state"] = 4
        return await update.message.reply_text("4️⃣ لینک پیج / فروشگاه / کسب‌وکار را بنویسید:")

    if state == 3:
        data["phone"] = text
        context.user_data["coop_state"] = 4
        return await update.message.reply_text("4️⃣ لینک پیج / فروشگاه / کسب‌وکار را بنویسید:")

    if state == 4:
        data["link"] = text
        context.user_data["coop_state"] = None

        user = update.message.from_user
        save_coop_request(user.id, user.username, data)

        # Notify admin
        admin_text = (
            "📥 درخواست همکاری جدید:\n\n"
            f"👤 نام: {data.get('full_name')}\n"
            f"📱 شماره: {data.get('phone')}\n"
            f"🔗 لینک: {data.get('link')}\n"
            f"🧩 نوع درخواست: {data.get('request_type')}\n"
            f"👤 User: @{user.username} (ID: {user.id})"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

        # Confirm to user
        confirm_text = (
            "✅ درخواست شما ثبت شد.\n"
            "⏳ درخواست شما حداکثر طی ۴۸ ساعت بررسی شده و با شما تماس گرفته خواهد شد."
        )
        return await update.message.reply_text(confirm_text)

    # Fallback if state is broken
    context.user_data["coop_state"] = None
    return await update.message.reply_text("خطا در فرم. لطفاً دوباره از منوی درخواست همکاری شروع کنید.")


# ============================
# MESSAGE HANDLER
# ============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # If user is in coop form flow
    if context.user_data.get("coop_state"):
        return await handle_coop_form(update, context)

    if text == "محصولات 🛍️":
        return await update.message.reply_text(
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=product_menu(),
        )

    if text == "راهنما 📖":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("اینستاگرام", url="https://www.instagram.com/apranik_perfume")],
            [InlineKeyboardButton("سایت", url="https://www.apranikperfume.com/fa")],
            [InlineKeyboardButton("تلگرام ادمین", url="https://t.me/apranik_perfume")],
        ])
        return await update.message.reply_text("لینک‌های مفید:", reply_markup=keyboard)

    if text == "درباره ما 🧾":
        about = (
            "✨ عطرساز و هنرمند رایحه ✨\n"
            "هر عطر یک اثر هنری دست‌سازه ❤️🔥\n"
            "ماموریت من خلق رایحه‌های ماندگار برای توست 🌟\n"
            "برای شروع سفارش /start را بفرست.\n\n"
            "ارتباط با ادمین:\n👉 https://t.me/apranik_perfume"
        )
        return await update.message.reply_text(about)

    if text == "درخواست همکاری 🤝":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ارسال درخواست همکاری 📝", callback_data="send_coop_request")]
        ])
        return await update.message.reply_text(
            "برای ارسال درخواست همکاری، روی دکمه زیر کلیک کنید:",
            reply_markup=keyboard,
        )

    return await update.message.reply_text("متوجه نشدم، لطفاً از منو استفاده کن.")


# ============================
# ERROR HANDLER
# ============================

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")


# ============================
# MAIN
# ============================

if __name__ == "__main__":
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error)

    print("Bot running...")
    app.run_polling()

