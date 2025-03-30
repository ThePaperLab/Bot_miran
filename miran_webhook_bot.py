import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from uuid import uuid4

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@yankuam78")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@miranpaper")

application = ApplicationBuilder().token(BOT_TOKEN).build()
PENDING_REQUESTS = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenutə nel nodo visivo di Miran.\n"
        "Inviami un'immagine per proporla al flusso collettivo.\n"
        "Tutto passa prima attraverso l’Occhio Terzo."
    )

# Photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    user_id = update.message.from_user.id
    request_id = str(uuid4())
    PENDING_REQUESTS[request_id] = (file_id, user_id)

    keyboard = [
        [
            InlineKeyboardButton("✅ Pubblica", callback_data=f"approve|{request_id}"),
            InlineKeyboardButton("❌ Annulla", callback_data=f"reject|{request_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_chat = await context.bot.get_chat(ADMIN_USERNAME)
    await context.bot.send_photo(
        chat_id=admin_chat.id,
        photo=file_id,
        caption="🖼️ Vuoi pubblicare questa immagine sul canale?",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "Hai mandato un’immagine. Non male.\n"
        "Ma non posso caricarla così, sai com’è.\n"
        "Prima deve passare il Giudizio dell’Occhio Terzo.\n"
        "Un essere umano — o qualcosa che gli somiglia — la guarderà, ci rifletterà, magari prenderà un caffè.\n"
        "Poi deciderà se è degna del canale o se finirà tra i ricordi non pubblicati.\n"
        "Ti aggiorno appena si muove qualcosa nell’ombra della moderazione."
    )

# Other content handler
async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Interazione non conforme.\n"
        "Questo nodo accetta soltanto frammenti visivi.\n"
        "Altri segnali saranno ignorati.\n"
        "Se cerchi parole, storie o risposte, devi varcare un’altra soglia:\n"
        "→ https://chatgpt.com/g/g-67defc5af8f88191a4a3e593921b46be-miran-paper"
    )

# Callback handler
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, request_id = query.data.split("|")

    data = PENDING_REQUESTS.pop(request_id, None)
    if not data:
        await query.edit_message_caption("❌ Richiesta non valida o già gestita.")
        return

    file_id, user_id = data

    if action == "approve":
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=file_id)
        await query.edit_message_caption("✅ Immagine pubblicata.")
        await context.bot.send_message(
            chat_id=user_id,
            text="Il Custode ha vagliato. L’immagine è passata.\n"
                 "È stata pubblicata nel flusso visivo collettivo.\n"
                 "Canale: https://t.me/MiranPaper\n"
                 "Un’altra tessera si aggiunge al mosaico."
        )
    else:
        await query.edit_message_caption("🚫 Pubblicazione annullata.")
        await context.bot.send_message(
            chat_id=user_id,
            text="L’Occhio Terzo ha parlato.\n"
                 "L’immagine è stata trattenuta.\n"
                 "Non verrà pubblicata.\n"
                 "Motivo segnalato: incongruenza narrativa\n"
                 "(ma potrebbe anche solo aver avuto una brutta giornata).\n"
                 "Prova con un altro frammento. O aspetta che cambino i venti."
        )

# Flask webhook endpoint
@app.post("/webhook")
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# Aggiunta handler
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(~filters.PHOTO, handle_other))
application.add_handler(CallbackQueryHandler(handle_approval))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
