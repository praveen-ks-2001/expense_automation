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

def load_google_credentials():
    """ Load Google credentials from file if available, else ask for JSON input. """
    try:
        with open("your_google_creds.json", "r") as file:
            creds_dict = json.load(file)
        print("✅ Loaded Google credentials from google_creds.json.")
    except FileNotFoundError:
        creds_json = input("🔑 Paste your Google credentials JSON here: ")
        creds_dict = json.loads(creds_json)  # Use input but don't save it
        print("✅ Google credentials loaded (not saved).")

    return creds_dict

def authenticate_google_sheets():
    """ Authenticate with Google Sheets using loaded credentials. """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = load_google_credentials()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    print("✅ Google Sheets authentication successful!")
    return client

def load_telegram_token():
    """ Load Telegram bot token from file if available, else ask for input. """
    try:
        with open("other_creds.json", "r") as file:
            other_creds = json.load(file)
        token = other_creds["access_token_telegram_bot"]
        print("✅ Loaded Telegram bot token from other_creds.json.")
    except FileNotFoundError:
        token = input("🤖 Enter your Telegram bot token: ").strip()
        print("✅ Telegram bot token loaded (not saved).")

    return token

# Example usage
client = authenticate_google_sheets()
BOT_TOKEN = load_telegram_token()


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

async def delete_last_transactions(update: Update, sheet_name: str, n: int):
    """ Delete the last N transactions from a sheet. """
    try:
        worksheet = client.open(file_name).worksheet(sheet_name)
        last_row = get_last_row(worksheet) - 1

        if last_row < 2:
            msg = f"📂 No transactions to delete in '{sheet_name}'."
        else:
            start_row = max(2, last_row - n + 1)
            worksheet.batch_clear([f"B{start_row}:D{last_row}"])
            msg = f"🗑️ Deleted last {n} transactions from '{sheet_name}'."

    except gspread.exceptions.WorksheetNotFound:
        msg = f"❌ Sheet '{sheet_name}' not found."

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
            for entry in transactions:
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

        elif text.lower() == ".info":
            msg = (
                "🤖 **Bot Commands:**\n"
                "1️⃣ `.sheet` - List available sheets.\n"
                "2️⃣ `.recent sheet_name,n` - Show last `n` transactions (default: 5).\n"
                "3️⃣ `.log sheet_name, amount, description` - Log a new transaction.\n"
                "4️⃣ `.delete sheet_name,n` - Delete last `n` transactions.\n"
                "5️⃣ `.info` - Show this help message."
            )
            await send_message(update, msg)
            
        elif text.lower().startswith(".recent"):
            parts = text[8:].split(",")  # Remove `.recent` and split the rest
            if len(parts) < 1:
                raise ValueError("Invalid .recent command format. Use: `.recent sheet_name,n`")

            sheet_name = parts[0].strip()
            n = int(parts[1].strip()) if len(parts) == 2 else 5
            await get_recent_transactions(update, sheet_name, n)

        elif text.lower().startswith(".log"):
            parts = text[4:].split(",")  # Remove `.log` and split the rest
            if len(parts) != 3:
                raise ValueError("Invalid .log command format. Use: `.log sheet_name, amount, description`")

            sheet_name, amount, description = [p.strip() for p in parts]
            amount = float(amount)
            await log_transaction(update, sheet_name, amount, description)

        elif text.lower().startswith(".delete"):
            parts = text[7:].split(",")  # Remove `.delete` and split the rest
            if len(parts) != 2:
                raise ValueError("Invalid .delete command format. Use: `.delete sheet_name,n`")

            sheet_name, n = parts[0].strip(), int(parts[1].strip())
            await delete_last_transactions(update, sheet_name, n)

        else:
            raise ValueError("Invalid command. Use `.info` for available commands.")

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
