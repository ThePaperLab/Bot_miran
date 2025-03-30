import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from uuid import uuid4

# Variabili d'ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@yankuam78")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@miranpaper")

# In memoria: mappa ID richieste → (file_id, user_id)
PENDING_REQUESTS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌬️ Benvenutə nel nodo visivo di Miran.
"
        "Inviami un'immagine per proporla al flusso collettivo.
"
        "Tutto passa prima attraverso l’Occhio Terzo."
    )

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
        "Hai mandato un’immagine. Non male.
"
        "Ma non posso caricarla così, sai com’è.

"
        "Prima deve passare il Giudizio dell’Occhio Terzo.
"
        "Un essere umano — o qualcosa che gli somiglia — la guarderà, ci rifletterà, magari prenderà un caffè. "
        "Poi deciderà se è degna del canale o se finirà tra i ricordi non pubblicati.

"
        "Ti aggiorno appena si muove qualcosa nell’ombra della moderazione."
    )

async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Interazione non conforme.

"
        "Questo nodo accetta soltanto frammenti visivi.
"
        "Altri segnali saranno ignorati.

"
        "Se cerchi parole, storie o risposte, devi varcare un’altra soglia:
"
        "→ https://chatgpt.com/g/g-67defc5af8f88191a4a3e593921b46be-miran-paper"
    )

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
            text="Il Custode ha vagliato. L’immagine è passata.
"
                 "È stata pubblicata nel flusso visivo collettivo.
"
                 "Canale: https://t.me/MiranPaper

"
                 "Un’altra tessera si aggiunge al mosaico."
        )
    else:
        await query.edit_message_caption("🚫 Pubblicazione annullata.")
        await context.bot.send_message(
            chat_id=user_id,
            text="L’Occhio Terzo ha parlato.

"
                 "L’immagine è stata trattenuta.
"
                 "Non verrà pubblicata.

"
                 "Motivo segnalato: incongruenza narrativa
"
                 "(ma potrebbe anche solo aver avuto una brutta giornata).

"
                 "Prova con un altro frammento. O aspetta che cambino i venti."
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO, handle_other))
    app.add_handler(CallbackQueryHandler(handle_approval))
    app.run_polling()

if __name__ == "__main__":
    main()
