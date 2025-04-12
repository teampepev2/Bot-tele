from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import asyncio
from utils.scraping import scrape_mod_links
from utils.database import init_db, save_user, get_referral_count
from config.config import BOT_TOKEN
import hashlib

# Shortlink provider rotasi (contoh dummy)
shortlink_providers = [
    "https://short1.example.com/api?link=",
    "https://short2.example.com/api?link=",
    "https://short3.example.com/api?link=",
    "https://short4.example.com/api?link="
]

def get_shortlink(original_url: str, user_id: int, game: str):
    hash_val = int(hashlib.md5(f"{user_id}-{game}".encode()).hexdigest(), 16)
    index = hash_val % len(shortlink_providers)
    return f"{shortlink_providers[index]}{original_url}"

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referred_by = int(args[0]) if args else None

    save_user(user.id, user.username, referred_by)

    keyboard = [[
        InlineKeyboardButton("🔍 Cari MOD", callback_data="search_mod"),
        InlineKeyboardButton("❤️ Simpan MOD", callback_data="saved_mod")
    ], [
        InlineKeyboardButton("👥 Referral Saya", callback_data="referral")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Halo {user.first_name}! Selamat datang di ModFinderBot.",
        reply_markup=reply_markup
    )

# --- CALLBACK ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search_mod":
        await query.message.reply_text("Ketik nama game yang ingin kamu cari MOD-nya.")
    elif query.data == "referral":
        count = get_referral_count(query.from_user.id)
        await query.message.reply_text(f"👥 Kamu telah mengundang {count} orang!")

# --- PENCARIAN MOD ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = update.message.text
    user_id = update.effective_user.id
    msg = await update.message.reply_text(f"🔎 Sedang mencari MOD untuk \"{game}\"...")

    await asyncio.sleep(2)
    raw_link = scrape_mod_links(game)
    if not raw_link:
        await msg.edit_text("❌ MOD tidak ditemukan. Coba lagi dengan nama lain.")
        return

    final_link = get_shortlink(raw_link, user_id, game)

    mod_text = f"""
🎮 *{game}*
🧩 MOD: Unlimited Coins & Keys  
🔧 Versi: v1.0.0  
📦 Ukuran: 150MB  
📥 [Download MOD]({final_link})
"""
    await msg.edit_text(mod_text, parse_mode="Markdown")

# --- MAIN ---
async def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot berjalan...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
