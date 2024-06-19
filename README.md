# Domain Scraper Bot

This repository contains a Python script for a Telegram bot that allows users to analyze domain availability, generate wordlists, and manage payments via cryptocurrencies.

## Features

- **Domain Extension Selection**: Set the domain extension to analyze (e.g., `.com`, `.it`).
- **Wordlist Generation**: Generate a wordlist based on keywords and combinations.
- **Domain Analysis**: Analyze the availability of specified domains.
- **File Management**: Specify and upload files for analysis.
- **Payments**: Manage payments via CoinPayments.
- **Multilingual**: Support for English and Italian.
- **User Profile**: View profile information and remaining credit.

## Requirements

- Python 3.8+
- Telegram Bot Token
- CoinPayments API Key and Secret

## Dependencies

Install the dependencies by running:

```bash
pip install -r requirements.txt
```
Configuration
Telegram Bot Token:

Obtain a token for your bot from BotFather.
Set the token in the config.py file or directly in the script.
CoinPayments:

Create an account on CoinPayments.
Obtain your COINPAYMENTS_API_KEY and COINPAYMENTS_API_SECRET.
Set these keys in the config.py file or directly in the script.
Usage
Run the bot with:

bash

python domain_scraper_bot.py
Once the bot is running, use the following commands:

/start: Start the bot and display the welcome message.
/lang <ENG|ITA>: Set the language.
/domain <extension>: Set the domain extension to analyze.
/setfile <file_path>: Specify the file to analyze.
/analyze: Start analyzing the specified domains.
/stop: Stop the ongoing analysis.
/list: View the analysis results.
/pay <amount> <currency> <email>: Initiate the payment process.
/credit: Check remaining credit.
/currency: View supported cryptocurrencies for payments.
/supported: View supported TLDs for analysis.
/profile: View user profile information.
/wordlist <word1> <word2> ... <wordN>: Generate a wordlist based on the provided words.
Configuration Example
python

TOKEN = "Your_Telegram_Token"
COINPAYMENTS_API_KEY = "Your_CoinPayments_API_Key"
COINPAYMENTS_API_SECRET = "Your_CoinPayments_API_Secret"
custom_domain_extension = '.com'  # Default domain extension
SCANSIONI_PER_EURO = 1000
FREE_SCANS = 150
DATA_FILE = 'user_data.csv'
OUTPUT_DIR = "wordlists"
DATAMUSE_API_URL = "https://api.datamuse.com/words"
Notes
The bot makes requests to the CoinPayments API and Datamuse API for payments and word synonyms.
Ensure you have appropriate error handling and security measures in place, especially for managing API keys and tokens.
Contributors
Feel free to contribute with improvements or bug reports.

This README covers the main aspects of your project, including features, requirements, configuration, and usage of the bot. You can certainly improve it over time with additional details or modifications based on user feedback.
