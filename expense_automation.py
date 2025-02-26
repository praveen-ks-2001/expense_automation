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


# Function to get the last N transactions from a sheet
def get_last_n_transactions(worksheet, n):
    col_b_values = worksheet.col_values(2)  # Fetch all values from column B (dates)
    last_row = len(col_b_values)  # Last filled row index
    
    if last_row < 2:  # Assuming row 1 is headers
        return []

    start_row = max(2, last_row - n + 1)  # Ensure we don't go below row 2
    return worksheet.get(f"B{start_row}:D{last_row}")  # Fetch last N rows from columns B, C, and D



# Function to get the last filled row in column B
def get_last_row(worksheet):
    col_b_values = worksheet.col_values(2)  # Fetch all values from column B
    return len(col_b_values) + 1  # Return the next available row


# Function to handle incoming messages
async def log_expense(update: Update, context: CallbackContext) -> None:
    text = update.message.text.strip()
    print(f"Text received: '{text}'")  # Debug log

    try:
        # Handle ".sheet" command to list available sheets
        if text.lower() == ".sheet":
            sheet = client.open(file_name)
            sheet_names = [ws.title for ws in sheet.worksheets()]
            msg = "📄 **Available Sheets:**\n" + "\n".join(sheet_names)

        # Handle ".recent <sheet_name> <count>" command
        elif text.lower().startswith(".recent"):
            parts = text.split()
            if len(parts) != 3:
                raise ValueError("Invalid .recent command format")

            sheet_name = parts[1]
            n = int(parts[2])  # Convert count to an integer

            # Open the specified sheet
            worksheet = client.open(file_name).worksheet(sheet_name)

            # Get last N transactions
            transactions = get_last_n_transactions(worksheet, n)

            if not transactions:
                msg = f"📂 No transactions found in '{sheet_name}'."
            else:
                msg = f"🔹 **Last {n} Transactions in '{sheet_name}':**\n"
                for entry in reversed(transactions):  # Reverse for latest-first order
                    date = (entry[0] if len(entry) > 0 else "-").ljust(12)  # Pad to 12 chars
                    amount = (entry[1] if len(entry) > 1 else "-").ljust(12)  # Pad to 12 chars
                    description = entry[2] if len(entry) > 2 else "-"  # No padding for description

                    msg += f" {date} | {amount} | {description}\n"

        # Handle normal expense logging
        else:
            parts = text.split(",")
            if len(parts) != 3:
                raise ValueError("Invalid input format")

            sheet_name, amount, description = [p.strip() for p in parts]
            amount = float(amount)  # Convert amount to float

            print(f"Processing entry -> Sheet: {sheet_name}, Amount: {amount}, Desc: {description}")  # Debug log

            # Open the specified sheet
            worksheet = client.open(file_name).worksheet(sheet_name)

            # Find the next available row in column B
            next_row = get_last_row(worksheet)
            print(f"Appending to row {next_row} in sheet {sheet_name}")  # Debug log

            # Append data with current date
            current_date = datetime.datetime.now(IST).strftime("%Y-%m-%d")
            worksheet.update(f"B{next_row}:D{next_row}", [[current_date, amount, description]])

            msg = f"✅ Expense Logged: {amount} on {description} in '{sheet_name}' at row {next_row}"

    except gspread.exceptions.WorksheetNotFound:
        msg = f"❌ Sheet '{sheet_name}' not found. Please check the name."

    except ValueError:
        msg = "❌ Invalid format. Please use: `.recent sheet_name count`"

    except Exception as e:
        msg = f"❌ Error: {str(e)}"

    now = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now}: {msg}")  # Debug log

    await update.message.reply_text(msg)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_expense))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
