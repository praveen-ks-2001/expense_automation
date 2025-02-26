import logging
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

file_name = "Bank Transfers 2025"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("your_google_creds.json", scope)
client = gspread.authorize(creds)

# Open and read the JSON file
with open("other_creds.json", "r") as file:
    other_creds = json.load(file)

# Telegram Bot Token
BOT_TOKEN = other_creds['access_token_telegram_bot']


# Function to handle incoming messages
async def log_expense(update: Update, context: CallbackContext) -> None:
    text = update.message.text.strip()
    print(f"Text received: '{text}'")

    # If user sends '/sheet', return available sheet names
    if text.lower() == ".sheet":
        try:
            sheet = client.open(file_name)
            print(1)
            sheet_names = [ws.title for ws in sheet.worksheets()]
            print(2)
            msg = "📄 Available Sheets:\n" + "\n".join(sheet_names)
            print(3)
        except Exception as e:
            msg = f"❌ Error fetching sheets: {str(e)}"

    else:
        try:
            sheet_name, amount, description = text.split(",")
            amount = float(amount.strip())
            sheet_name = sheet_name.strip()
            description = description.strip()

            # Open the specified sheet
            worksheet = client.open(file_name).worksheet(sheet_name)

            # Append data with current date
            current_date = datetime.datetime.now(IST).strftime("%Y-%m-%d")
            worksheet.append_row([current_date, amount, description])

            msg = f"✅ Expense Logged: {amount} on {description} in '{sheet_name}'"

        except gspread.exceptions.WorksheetNotFound:
            msg = f"❌ Sheet '{sheet_name}' not found. Please check the name."

        except ValueError:
            msg = "❌ Invalid format. Please use: `sheet_name,amount,description`"

        except Exception as e:
            msg = f"❌ Error: {str(e)}"

    now = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now}: {msg}")

    await update.message.reply_text(msg)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_expense))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()