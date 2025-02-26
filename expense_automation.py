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


def get_last_n_transactions(worksheet, n):
    """ Fetch the last N transactions from a sheet. """
    col_b_values = worksheet.col_values(2)
    last_row = len(col_b_values)

    if last_row < 2:
        return []

    start_row = max(2, last_row - n + 1)
    return worksheet.get(f"B{start_row}:D{last_row}")


def get_last_row(worksheet):
    """ Get the next available row in column B. """
    col_b_values = worksheet.col_values(2)
    return len(col_b_values) + 1


async def list_sheets(update: Update):
    """ List available sheets. """
    sheet = client.open(file_name)
    sheet_names = [ws.title for ws in sheet.worksheets()]
    msg = "📄 **Available Sheets:**\n" + "\n".join(sheet_names)
    await send_message(update, msg)


async def get_recent_transactions(update: Update, sheet_name: str, n: int = 5):
    """ Fetch and display recent transactions from a sheet. """
    try:
        worksheet = client.open(file_name).worksheet(sheet_name)
        transactions = get_last_n_transactions(worksheet, n)

        if not transactions:
            msg = f"📂 No transactions found in '{sheet_name}'."
        else:
            msg = f"🔹 **Last {n} Transactions in '{sheet_name}':**\n"
            for entry in reversed(transactions):
                date = entry[0] if len(entry) > 0 else "-"
                amount = entry[1] if len(entry) > 1 else "-"
                description = entry[2] if len(entry) > 2 else "-"
                msg += f"{date:<12} | {amount:<12} | {description}\n"

    except gspread.exceptions.WorksheetNotFound:
        msg = f"❌ Sheet '{sheet_name}' not found."

    await send_message(update, msg)


async def log_transaction(update: Update, sheet_name: str, amount: float, description: str):
    """ Log a new transaction in a sheet. """
    try:
        worksheet = client.open(file_name).worksheet(sheet_name)
        next_row = get_last_row(worksheet)

        current_date = datetime.datetime.now(IST).strftime("%Y-%m-%d")
        worksheet.update(range_name=f"B{next_row}:D{next_row}", values=[[current_date, amount, description]])

        msg = f"✅ Expense Logged: {amount} on {description} in '{sheet_name}' at row {next_row}"
    
    except gspread.exceptions.WorksheetNotFound:
        msg = f"❌ Sheet '{sheet_name}' not found."

    await send_message(update, msg)


async def send_message(update: Update, msg: str):
    """ Send message in chunks if it exceeds Telegram's 4096 character limit. """
    MAX_TELEGRAM_MSG_LENGTH = 4096
    msg_parts = [msg[i:i+MAX_TELEGRAM_MSG_LENGTH] for i in range(0, len(msg), MAX_TELEGRAM_MSG_LENGTH)]

    for part in msg_parts:
        await update.message.reply_text(part)


async def handle_message(update: Update, context: CallbackContext):
    """ Handle incoming messages and route them to appropriate functions. """
    text = update.message.text.strip()
    print(f"Text received: '{text}'")

    try:
        if text.lower() == ".sheet":
            await list_sheets(update)

        elif text.lower().startswith(".recent"):
            parts = text.split()
            if len(parts) < 2:
                raise ValueError("Invalid .recent command format")

            sheet_name = parts[1]
            n = int(parts[2]) if len(parts) == 3 else 5
            await get_recent_transactions(update, sheet_name, n)

        else:
            parts = text.split(",")
            if len(parts) != 3:
                raise ValueError("Invalid input format")

            sheet_name, amount, description = [p.strip() for p in parts]
            amount = float(amount)
            await log_transaction(update, sheet_name, amount, description)

    except ValueError as e:
        msg = f"❌ Error: {str(e)}"
        await send_message(update, msg)

    except Exception as e:
        msg = f"❌ Unexpected error: {str(e)}"
        await send_message(update, msg)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
