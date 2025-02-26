import logging
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

SHEET_NAME = "Bank Transfers 2025"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("your_google_creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# Open and read the JSON file
with open("other_creds.json", "r") as file:
    other_creds = json.load(file)

# Telegram Bot Token
BOT_TOKEN = other_creds['access_token_telegram_bot']


# Function to handle incoming messages
async def log_expense(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    try:
        source, amount, category = text.split(",")
        amount = float(amount)
        
        # Append data to Google Sheet
        sheet.append_row([update.message.date.strftime("%Y-%m-%d"), source.strip(), amount, category.strip()])
        
        await update.message.reply_text(f"✅ Expense Logged: {source} spent {amount} on {category}")  # ✅ Await added
    except Exception as e:
        await update.message.reply_text("❌ Invalid format. Please use: `source,amount,category`")  # ✅ Await added


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_expense))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()