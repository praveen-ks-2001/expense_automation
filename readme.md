# Telegram Expense Tracker Bot

This bot allows you to log and retrieve transactions from a Google Sheet via Telegram commands. It uses the Telegram Bot API and Google Sheets API for managing financial records.

## 🚀 Features

- Log expenses directly from Telegram.
- Retrieve the latest transactions from a sheet.
- List available sheets in the Google Spreadsheet.
- Delete transactions by ID.
- Easy setup with Google and Telegram API credentials.

## 📌 Prerequisites

Before running this script, ensure you have:

- Python 3.x installed.
- A **Telegram Bot Token** from [BotFather](https://t.me/botfather).
- A **Google Service Account** with access to Google Sheets.
- Required Python libraries listed in `requirements.txt`. Install them using:
  ```sh
  pip install -r requirements.txt
  ```

## 🛠 Setup Instructions

### 1️⃣ Set Up Google Sheets API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Google Sheets API**.
3. Create a **Service Account** and download the JSON credentials file.
4. Share access of your Google Sheet with the service account email (ending in `@iam.gserviceaccount.com`).
5. Rename and place the JSON file as `your_google_creds.json` in the same directory as the script.

### 2️⃣ Set Up Telegram Bot

1. Open [BotFather](https://t.me/botfather) on Telegram and create a bot.
2. Copy the **bot token** provided by BotFather.
3. Save the token in a file named `other_creds.json` in this format:
   ```json
   {
     "access_token_telegram_bot": "YOUR_TELEGRAM_BOT_TOKEN"
   }
   ```

### 3️⃣ Configure the Spreadsheet

1. Open Google Sheets and create a new spreadsheet.
2. Name it (default: `Bank Transfers 2025`) or update the variable `file_name` in the script.
3. See the sample sheet uploaded which works with the code. You can tweak the code for the format you require. [SampleSheet](https://docs.google.com/spreadsheets/d/1vaDPWdwSa7v4Mp1Hri7iRbngS6EOuDLsK6VLyCWXcNo/edit?usp=sharing)

### 4️⃣ Install Dependencies & Run the Bot

```sh
pip install -r requirements.txt
python expense_automation.py
```

## 📝 Commands

| Command                                | Description                                                         |
| -------------------------------------- | ------------------------------------------------------------------- |
| `.sheet`                               | Lists available sheets in the Google Spreadsheet.                   |
| `.recent sheet_name, [n]`              | Retrieves the last `n` transactions (default: 5) from `sheet_name`. |
| `.log sheet_name, amount, description` | Logs a new transaction in `sheet_name`.                             |
| `.delete sheet_name, transaction_id`   | Deletes a transaction by its ID in `sheet_name`.                    |
| `.info`                                | Shows a list of available commands.                                 |

## 🛠 Troubleshooting

- **Google Sheets authentication failed?**
  - Ensure the service account has access to the sheet.
  - Make sure the correct JSON credentials file is used.

- **Bot not responding?**
  - Check if the bot token is correct in `other_creds.json`.
  - Ensure your bot is running in a terminal.

## 🏆 Credits

Developed by **pk**

---

Happy Tracking! 🚀