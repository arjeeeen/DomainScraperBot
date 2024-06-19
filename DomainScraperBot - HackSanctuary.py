import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from colorama import Fore, Style, init
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, JobQueue, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError
import os
import asyncio
import hashlib
import hmac
import csv
from urllib.parse import urlencode
import tracemalloc
from requests.adapters import HTTPAdapter
import json
import httpx
from datetime import datetime, timedelta
from itertools import permutations
from itertools import combinations
from nltk.corpus import wordnet
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nltk
import time
nltk.download('wordnet')

tracemalloc.start()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_TOKEN")
COINPAYMENTS_API_KEY = os.getenv("COINPAYMENTS_API_KEY")
COINPAYMENTS_API_SECRET = os.getenv("COINPAYMENTS_API_SECRET")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
custom_domain_extension = '.com'  # Estensione di dominio predefinita
SCANSIONI_PER_EURO = 1000
FREE_SCANS = 150
DATA_FILE = 'user_data.csv'
scheduler = None
OUTPUT_DIR = "wordlists"
DATAMUSE_API_URL = "YOUR_API"

init(autoreset=True)

# Memorizzazione persistente
user_profiles = {}
user_files = {}
user_tasks = {}
partial_results = {}
user_payments = {}
user_credits = {}
user_file_counts = {}
user_lang = {}


MIN_PAYMENT_AMOUNT = 1  # Importo minimo di pagamento in EUR

# Definire i testi in due lingue: INGLESE e ITALIANO
TEXTS = {
    'ENG': {
        'language_set': '🇬🇧 Language set as English. /start For run the bot',
        'language_error': 'Please specify a valid language (ENG or ITA)',
        'example_text': 'This is an example text in English.',
        'welcome_message': '''💫🌟 Domain Scraper Bot 🌟💫 

This is the list to make bot work properly:

🛰️  /domain to choose the domain extension (e.g. .com, .it etc..)
🎆  /wordlist if you need to generate a dictionary 
📁  /setfile <file_path> to specify the file to analyze
👀  /analyze to start analyzing domains 
🛑  /stop to stop the analysis 
📋  /list to see the results 
💸  /pay <amount> <currency> <email> to make a payment
💎  /credit to check the remaining credit
💱  /currency to find out which crypto we accept
📔  /supported to control which TLDs we support
🌍  /lang to change language
🕵️  /profile to view your profile information

👁️‍🗨️  Remember, each €1 deposited equals 1000 domain scans!''',
        'profile_saved': '🔍 User profile saved:\n\nID: {user_id}\nUsername: {username}\nFirst Name: {first_name}\nLast Name: {last_name}\nCredits: {credits:.2f} €\nAvailable Scans: {scans}\nFree scans remaining: {free_scans}',
        'file_not_found_error': 'The file {inputfile} was not found.',
        'invalid_language_message': '''Please specify a valid language. Use: 
        '/lang ENG' for English 🇬🇧
        '/lang ITA' for Italian 🇮🇹''',
        'request_error': 'Error in the request for {domain}: {error}',
        'supported_currencies_success': 'Supported cryptocurrencies:\n{currency_list}',
        'supported_currencies_error': 'Error retrieving supported cryptocurrencies: {error}',
        'payment_usage': '''Usage:
/pay <amount> <currency> <email>
Example: /pay 1 LTC email@gmail.com

🤓 PS: <currency> is in EURO !''',
        'min_payment_amount_error': 'The minimum payment amount is {MIN_PAYMENT_AMOUNT}€. Please increase the amount and try again.',
        'currency_not_supported': 'The cryptocurrency {currency} is not supported. Use /supported_currencies to see the supported cryptocurrencies.',
        'payment_success': '''🫰 Payment successfully created. Please use this link to pay: {status_url}
        Don't do anything. Stay here and wait feedback''',
        'payment_status_success': '💰 Payment successfully completed! You have a credit of {credits:.2f}€.',
        'payment_status_error': '❌ Error during payment verification. Please try again.',
        'credit_message': 'You have a credit of {credit:.2f}€, which equals {scans} domain scans.',
        'domain_set_success': '🛸 Domain extension set: {extension}',
        'domain_set_error': '💀 You need to specify a domain extension. Example: /domain .it',
        'available_domains': 'Available domains:\n{domains}',
        'no_domains_found': 'No available domains found or the file does not exist.',
        'no_file_specified': 'You have not specified any file. Use the /setfile command to specify the file to analyze.',
        'file_set_success': '🛸 File set: {file_path}',
        'file_not_exist': 'The file {file_path} does not exist.',
        'file_path_not_specified': '''💀 You need to specify the file path. 
        Use the command /setfile <file_path>''',
        'analysis_in_progress': 'Analysis already in progress. Use the /stop command to interrupt it.',
        'file_and_extension_not_set': '💀 You need to set the file to analyze and the domain extension before starting the analysis.',
        'payment_required': '💀 You need to make a payment before starting the analysis. Use /pay to make a payment.',
        'domain_analysis_start': '''🚀 Starting domain analysis...

You can stop the bot whatever you want with /stop''',
        'domain_analysis_progress': '''🚀 Analyzed {current} out of {total} domains... 

You can stop the bot whatever you want with /stop''',
        'domain_analysis_complete': '✅Analysis complete.',
        'domain_analysis_html_ready': '🧙 Analysis complete. Use the /list command to download the HTML file with the results.',
        'domain_analysis_error': 'Error during analysis: {error}',
        'domain_analysis_interrupted': '✅ Use the /list command to download the HTML file with the results.',
        'html_title': 'Domain Verification Results',
        'html_header': 'Domain Verification Results',
        'html_comprabili': '✅ Available Domains',
        'html_in_uso': '❌ Domains Already in Use',
        'analysis_stopped': '⛔ Analysis stopped.',
        'no_analysis_in_progress': '💀 No analysis in progress.',
        'no_domains_analyzed': '💀 No domains have been analyzed yet or you provided an incorrect file.',
        'analysis_not_started': '💀 You need to start the domain analysis before you can view the results.',
        'min_payment_scans_error': 'The minimum payment amount is {MIN_PAYMENT_AMOUNT}€. Please increase the amount and try again. This will give you {scans} domain scans.',
        'credit_message': '💎 You have a credit of {credit:.2f}€, which equals {scans} domain scans.',
        'scan_limit_reached': '💀 You have reached your scan limit. Please add more credits to continue scanning domains.',
        'profile_saved': '🔍 User profile:\n\nID: {user_id}\nUsername: {username}\nFirst Name: {first_name}\nLast Name: {last_name}\nCredits: {credits:.2f} EUR\nAvailable Scans: {scans}\nFree scans remaining: {free_scans}',
        'file_extension_error': '❌ Only .txt or .csv files are supported.',
        'file_upload_success': '''🛸 File uploaded successfully: {file_name}
        
You can start the bot with /analyze''',
        'file_path_not_specified': '''💀 You need to specify the file path. 
        Use /setfile <file_path> or upload the file directly with Telegram!''',
        'payment_pending': '🕒 Payment pending. Awaiting confirmations, wait...',
        'payment_wait_feedback': '🕒 Payment created successfully. Please use this link to pay: {status_url}\nDon\'t do anything. Stay here and wait for feedback.',
        'payment_successful': '✅ Payment successful! You have been credited {scans} scans.',
        'payment_failed': '❌ Payment failed or cancelled.',
        'payment_error': '❌ Error: {error}',
        'payment_status_unknown': '🔍 In few minutes...',
        'invalid_payment_amount': "❌ The amount must be a positive integer. Please try again with a valid amount.",
        'timeout_error': '❌ A timeout occurred while fetching the document. Please try again later or contact support',
        'supp_TLDs': '📔 We support TLDs like: \n.com \n.me \n.net \n.org \n.sh \n.io \n.co \n.club \n.biz \n.mobi \n.info \n.us \n.domains \n.cloud \n.fr \n.au \n.ru \n.uk \n.nl \n.fi \n.br \n.hr \n.ee \n.ca \n.sk \n.se \n.no \n.cz \n.it \n.in \n.icu \n.top \n.xyz \n.cn \n.cf \n.hk \n.sg \n.pt \n.site \n.kz \n.si \n.ae \n.do \n.yoga \n.xxx \n.ws \n.work \n.wiki \n.watch \n.wtf \n.world \n.website \n.vip \n.ly \n.dev \n.network \n.company \n.page \n.rs \n.run \n.science \n.sex \n.shop \n.solutions \n.so \n.studio \n.style \n.tech \n.travel \n.vc \n.pub \n.pro \n.app \n.press \n.ooo \n.de',
        'free_scan_finished': '🏁 You have finished the free version. If you liked the bot, consider purchasing it. It\'s cheap!',
        'restart_bot_message': '''💾 Save the file, because it will be deleted in 30 minutes!!
        
💡 If you want to use the bot again use /start''',
        'provide_wordlist': '''You need to provide between 3 and 10 words.
        
Example: /wordlist hacker animal computer jesus''',
        'enter_unique_word_count': 'Please enter the number of unique words for the dictionary.',
        'first_use_command': 'First use the /wordlist to provide words.',
        'enter_valid_number': 'Please enter a valid number.',
        'error_fetching_synonyms': '❌ Error fetching synonyms for {word}: {status_code}.',
        'file_generated_successfully': '✅ Wordlist file generated successfully.',
        'use_as_scan_file': '💾 Do you want to use it as the file to scan domains?',
        'yes_button': 'Yes',
        'no_button': 'No',
        'file_generation_start': '🗃️ Starting generation file... {progress}%',
        'file_generation_in_progress': '🗃️ Work in progress... {progress}%',
    },
    'ITA': {
        'language_set': '🇮🇹 Lingua impostata come Italiano. /start Per far partire il bot',
        'language_error': 'Specifica una lingua valida (ENG o ITA)',
        'example_text': 'Questo è un testo di esempio in italiano.',
        'welcome_message': '''💫🌟 Domain Scraper Bot 🌟💫
        
Questa è la lista per utilizzare correttamente il bot:

🛰️  /domain scegli l'estensione del dominio (.com, .it ecc..) 
🎆  /wordlist se hai bisogno di creare un dizionario
📁  /setfile <percorso_file> per specificare il file da analizzare
👀  /analyze per avviare l'analisi dei domini 
🛑  /stop per interrompere l'analisi 
📋  /list per visualizzare i risultati 
💸  /pay <importo> <valuta> <email> per effettuare un pagamento
💎  /credit per verificare il credito rimanente
💱  /currency per sapere che crypto accettiamo
📔  /supported per sapere che TLDs accettiamo
🌍  /lang per cambiare lingua
🕵️  /profile per visualizzare le informazioni del tuo profilo

👁️‍🗨️  Ricorda, ogni €1 depositato equivale a 1000 scansioni dominio!''',
        'profile_saved': '🔍 Profilo utente salvato:\n\nID: {user_id}\nUsername: {username}\nNome: {first_name}\nCognome: {last_name}\nCrediti: {credits:.2f} EUR\nScansioni disponibili: {scans}\nScansioni gratuite rimanenti: {free_scans}',
        'file_not_found_error': 'Il file {inputfile} non è stato trovato.',
        'invalid_language_message': '''Specifica una lingua valida. Usa:
        '/lang ENG' per l'inglese 🇬🇧
        '/lang ITA' per l'italiano 🇮🇹''',
        'request_error': 'Errore nella richiesta per {domain}: {error}',
        'supported_currencies_success': 'Criptovalute supportate:\n{currency_list}',
        'supported_currencies_error': 'Errore nel recupero delle criptovalute supportate: {error}',
        'payment_usage': '''Utilizzo: 
/pay <importo> <valuta> <email>
Esempio: /pay 1 LTC email@gmail.com

🤓 PS: <currency> è in EURO !''',
        'min_payment_amount_error': 'L\'importo minimo per un pagamento è {MIN_PAYMENT_AMOUNT}€. Per favore, incrementa l\'importo e riprova.',
        'currency_not_supported': 'La criptovaluta {currency} non è supportata. Usa /supported_currencies per vedere le criptovalute supportate.',
        'payment_success': '''🫰 Pagamento creato con successo. Per favore, utilizza questo link per pagare: {status_url}
        Non fare altro, attendi il pagamento completato!!''',
        'payment_status_success': '💰 Pagamento completato con successo! Hai un credito di {credits:.2f}€.',
        'payment_status_error': '❌ Errore durante la verifica del pagamento. Si prega di riprovare.',
        'credit_message': 'Hai un credito di {credit:.2f}€, equivalgono a {scans} domini da scansionare.',
        'domain_set_success': '🛸 Estensione di dominio impostata: {extension}',
        'domain_set_error': '💀 Devi specificare un\'estensione di dominio. Esempio: /domain .it',
        'available_domains': 'Domini disponibili:\n{domains}',
        'no_domains_found': 'Nessun dominio disponibile trovato o il file non esiste.',
        'no_file_specified': 'Non hai specificato alcun file. Usa il comando /setfile per specificare il file da analizzare.',
        'file_set_success': '🛸 File impostato: {file_path}',
        'file_not_exist': 'Il file {file_path} non esiste.',
        'file_path_not_specified': '''💀 Devi specificare il percorso del file. 
        Usa il comando /setfile <percorso_file>''',
        'analysis_in_progress': 'Analisi già in corso. Usa il comando /stop per interromperla.',
        'file_and_extension_not_set': '💀 Devi impostare il file da analizzare e l\'estensione del dominio prima di avviare l\'analisi.',
        'payment_required': '💀 Devi effettuare un pagamento prima di avviare l\'analisi. Usa /pay per effettuare un pagamento.',
        'domain_analysis_start': '''🚀 Inizio dell\'analisi del dominio...
        
Ricorda che puoi fermare il bot quando vuoi, con /stop''',
        'domain_analysis_progress': '''🚀 Analizzati {current} su {total} domini...

Ricorda che puoi fermare il bot quando vuoi, con /stop''',
        'domain_analysis_complete': '✅ Analisi completata.',
        'domain_analysis_html_ready': '🧙 Usa il comando /list per scaricare il file HTML con i risultati.',
        'domain_analysis_error': 'Errore durante l\'analisi: {error}',
        'domain_analysis_interrupted': '✅ Usa il comando /list per scaricare il file HTML con i risultati.',
        'html_title': 'Risultati Verifica Domini',
        'html_header': 'Risultati Verifica Domini',
        'html_comprabili': '✅ Domini Disponibili',
        'html_in_uso': '❌ Domini Già in Uso',
        'analysis_stopped': '⛔ Analisi interrotta.',
        'no_analysis_in_progress': '💀 Nessuna analisi in corso.',
        'no_domains_analyzed': '💀 Nessun dominio è stato analizzato o hai fornito un file errato.',
        'analysis_not_started': '💀 Devi avviare l\'analisi del dominio prima di poter visualizzare i risultati.',
        'min_payment_scans_error': 'L\'importo minimo per un pagamento è {MIN_PAYMENT_AMOUNT}€. Per favore, incrementa l\'importo e riprova. Questo ti permetterà di eseguire {scans} scansioni di domini.',
        'credit_message': '💎 Hai un credito di {credit:.2f}€, che equivale a {scans} scansioni di domini.',
        'scan_limit_reached': '💀 Hai raggiunto il limite delle scansioni. Aggiungi più credito per continuare a scansionare i domini.',
        'profile_saved': '🔍 Profilo utente:\n\nID: {user_id}\nUsername: {username}\nNome: {first_name}\nCognome: {last_name}\nCrediti: {credits:.2f} €\nScansioni disponibili: {scans} \nScansioni gratuite rimenenti: {free_scans}',
        'file_extension_error': '❌ Sono supportati solo file .txt o .csv.',
        'file_upload_success': '''🛸 File caricato con successo: {file_name}
        
Puoi far partire l'analisi con /analyze''',
        'file_path_not_specified': '''💀 Devi specificare il percorso del file. f
        Usa il comando /setfile <percorso_file> oppure carica il file direttamente!''',
        'payment_pending': '🕒 Pagamento in corso! In attesa di conferme.',
        'payment_wait_feedback': '🕒 Pagamento creato con successo. Per favore usa questo link per pagare: {status_url}\nNon fare nulla. Rimani qui e attendi il feedback.',
        'payment_successful': '✅ Pagamento riuscito! Hai ottenuto {scans} scansioni.',
        'payment_failed': '❌ Pagamento fallito o annullato.',
        'payment_error': '❌ Errore: {error}',
        'payment_status_unknown': '🔍 Ci siamo quasi...',
        'invalid_payment_amount': "❌ L'importo deve essere una cifra intera positiva. Per favore, riprova con un importo valido.",
        'timeout_error': '❌ Si è verificato un timeout durante il recupero del documento. Riprova più tardi o contatta il supporto.',
        'supp_TLDs': '📔 Supportiamo TLDs come: \n.com \n.me \n.net \n.org \n.sh \n.io \n.co \n.club \n.biz \n.mobi \n.info \n.us \n.domains \n.cloud \n.fr \n.au \n.ru \n.uk \n.nl \n.fi \n.br \n.hr \n.ee \n.ca \n.sk \n.se \n.no \n.cz \n.it \n.in \n.icu \n.top \n.xyz \n.cn \n.cf \n.hk \n.sg \n.pt \n.site \n.kz \n.si \n.ae \n.do \n.yoga \n.xxx \n.ws \n.work \n.wiki \n.watch \n.wtf \n.world \n.website \n.vip \n.ly \n.dev \n.network \n.company \n.page \n.rs \n.run \n.science \n.sex \n.shop \n.solutions \n.so \n.studio \n.style \n.tech \n.travel \n.vc \n.pub \n.pro \n.app \n.press \n.ooo \n.de',
        'free_scan_finished': '🏁 Hai finito la versione gratuita. Se ti è piaciuto il bot, considera di acquistarlo. Costa poco!',
        'restart_bot_message': '''💾 Salva il file, perchè tra 30 minuti verrà eliminato!
        
💡 Se vuoi utilizzare di nuovo il bot usa /start''',
        'provide_wordlist': '''ℹ️ Devi fornire tra 3 e 10 parole

Esempio: /wordlist hacker animal computer jesus''',
        'enter_unique_word_count': 'Inserisci il numero di parole uniche per il dizionario.',
        'first_use_command': 'Prima utilizza il comando /wordlist per fornire le parole.',
        'enter_valid_number': 'Inserisci un numero valido.',
        'error_fetching_synonyms': '❌ Errore nel recuperare i sinonimi per {word}: {status_code}.',
        'file_generated_successfully': '✅ File del dizionario generato con successo!',
        'use_as_scan_file': '💾  Vuoi usarlo come file per scansionare i domini?',
        'yes_button': 'Sì',
        'no_button': 'No',
        'file_generation_start': '🗃️ Inizia la generazione del file... {progress}%',
        'file_generation_in_progress': '🗃️ Generazione del file... {progress}%',
    }
}

def delete_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    response = requests.get(url)
    if response.status_code == 200:
        logger.info("Webhook eliminato con successo.")
    else:
        logger.error(f"Errore nell'eliminare il webhook: {response.text}")

def load_user_data():
    if not os.path.exists(DATA_FILE):
        return {}
    
    user_data = {}
    with open(DATA_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            user_id = int(row['user_id'])
            user_data[user_id] = {
                'credits': int(row['credits']),
                'username': row['username'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'free_scans_remaining': int(row.get('free_scans_remaining', FREE_SCANS))
            }
    return user_data

def save_user_data(user_data):
    with open(DATA_FILE, 'w', newline='') as csvfile:
        fieldnames = ['user_id', 'credits', 'username', 'first_name', 'last_name', 'free_scans_remaining']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for user_id, data in user_data.items():
            writer.writerow({
                'user_id': user_id,
                'credits': data.get('credits', 0),
                'username': data.get('username', ''),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'free_scans_remaining': data.get('free_scans_remaining', FREE_SCANS)
            })

def delete_file(file_path):
    # Controlla se il file esiste
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"File {file_path} eliminato con successo.")
    else:
        logger.error(f"Tentativo di eliminare il file fallito: {file_path} non trovato.")

def get_synonyms(word, language):
    """Fetch synonyms from Datamuse API."""
    params = {'rel_syn': word}
    response = requests.get(DATAMUSE_API_URL, params=params)
    if response.status_code == 200:
        words = response.json()
        return [entry['word'] for entry in words]
    else:
        logger.error(TEXTS[language]['error_fetching_synonyms'].format(word=word, status_code=response.status_code))
        return []

def generate_concatenated_combinations(words):
    """Generate concatenated combinations of words without spaces."""
    concatenated_words = set()
    word_list = list(words)
    for comb in combinations(word_list, 2):
        concatenated_words.add(''.join(comb))  # Combine as is
        concatenated_words.add(''.join(comb[::-1]))  # Combine in reverse order
    return concatenated_words

async def wordlist(update: Update, context: CallbackContext) -> None:
    user_language = user_lang.get(update.message.from_user.id, 'ENG')

    # Verifica il numero di parole fornite
    words = context.args
    if len(words) < 3 or len(words) > 10:
        response = TEXTS[user_language]['provide_wordlist']
        await update.message.reply_text(response)
        return
    
    # Salva le parole nei dati del contesto utente
    context.user_data['words'] = words

    # Avvia la generazione del dizionario senza chiedere ulteriori input
    await generate_wordlist(update, context)

async def generate_wordlist(update: Update, context: CallbackContext) -> None:
    user_language = user_lang.get(update.message.from_user.id, 'ENG')
    user_id = update.message.from_user.id
    username = update.message.from_user.username or str(user_id)

    global user_file_counts

    # Inizializza il conteggio dei file per l'utente se non esiste
    if user_id not in user_file_counts:
        user_file_counts[user_id] = 0

    # Incrementa il conteggio dei file per l'utente
    user_file_counts[user_id] += 1
    file_count = user_file_counts[user_id]

    # Verifica se abbiamo una lista di parole salvata
    if 'words' not in context.user_data:
        response = TEXTS[user_language]['first_use_command']
        await update.message.reply_text(response)
        return

    # Genera il dizionario con parole uniche basato sui sinonimi da Datamuse e concatenate
    base_words = context.user_data['words']
    unique_words = set(base_words)  # Include initially provided words

    # Trova sinonimi delle parole fornite
    for word in base_words:
        synonyms = get_synonyms(word, user_language)
        # Filtra fuori parole con spazi
        synonyms = [syn for syn in synonyms if ' ' not in syn]
        unique_words.update(synonyms)

    # Genera combinazioni concatenate senza spazi
    concatenated_combinations = generate_concatenated_combinations(unique_words)
    unique_words.update(concatenated_combinations)

    # Creare il file di output con parole uniche
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    file_name = f"{username}_{file_count}.txt"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    words_list = list(unique_words)
    total_words = len(words_list)

    # Inizializza il messaggio di attesa
    message = await update.message.reply_text(TEXTS[user_language]['file_generation_start'].format(progress=0))

    with open(file_path, 'w', encoding='utf-8') as f:
        for i, word in enumerate(words_list):
            f.write(word + "\n")

            # Aggiorna la percentuale di completamento per ogni 10% raggiunto
            if (i + 1) % (total_words // 10) == 0:
                percent_complete = ((i + 1) / total_words) * 100
                await message.edit_text(TEXTS[user_language]['file_generation_in_progress'].format(progress=int(percent_complete)))

    # Inviare il file all'utente
    with open(file_path, 'rb') as file:
        await update.message.reply_document(document=InputFile(file, filename=file_name))

    response = TEXTS[user_language]['file_generated_successfully']
    await update.message.reply_text(response)

    # Invia pulsanti "Sì" e "No"
    keyboard = [
        [
            InlineKeyboardButton(TEXTS[user_language]['yes_button'], callback_data=f"set_file|{file_name}"),
            InlineKeyboardButton(TEXTS[user_language]['no_button'], callback_data='no'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS[user_language]['use_as_scan_file'], reply_markup=reply_markup)

    # Pulire i dati dell'utente
    del context.user_data['words']

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_language = user_lang.get(query.message.chat.id, 'ENG')

    # Handle the user's response to the buttons
    callback_data = query.data
    if callback_data.startswith("set_file"):
        _, file_name = callback_data.split("|")
        # Set this file as the file to scan domains
        user_files[query.message.chat.id] = os.path.join(OUTPUT_DIR, file_name)
        await query.edit_message_text(text=TEXTS[user_language]['file_set_success'].format(file_path=file_name))
    else:
        # If the user clicked "No"
        await query.edit_message_text(text=TEXTS[user_language]['file_generated_successfully'])
        await start(update, context)

def leggiparoleconcom(inputfile):
    try:
        with open(inputfile, 'r') as file:
            parole = file.readlines()
        
        parolecon = [parola.strip() + custom_domain_extension for parola in parole]
        
        return parolecon
    except FileNotFoundError:
        print(f"{Fore.RED}Il file {inputfile} non è stato trovato.{Style.RESET_ALL}")
        return []

def check_domain_availability(domain):
    url = f"https://api.apilayer.com/whois/query?domain={domain}"
    payload = {}
    headers = {
        "apikey": "EWX8XffVKcTBzR9XkF9pEewJ3FKyIXQE"
    }

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response_json = response.json()

        # Verifica se 'result' è un dizionario e contiene 'status'
        if "result" in response_json and isinstance(response_json["result"], dict):
            status = response_json["result"].get("status", "")
            if isinstance(status, list):
                # Unisci la lista in una singola stringa per utilizzare upper()
                status = " ".join(status)
            if "AVAILABLE" in status.upper():
                return "AVAILABLE DOMAIN"

        # Verifica se contiene 'message' con 'AVAILABLE' o 'not found'
        if ("result" in response_json and response_json["result"] == "not found") or ("message" in response_json and "AVAILABLE" in response_json["message"].upper()):
            return "AVAILABLE DOMAIN"

        # Per i casi rimanenti, restituisci l'intera risposta JSON come stringa
        return response_json
    except requests.RequestException as e:
        print(f"{Fore.RED}Request error for {domain}: {e}{Style.RESET_ALL}")
        return None

def leggi_domini_disponibili(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as file:
        lines = file.readlines()
    domini_disponibili = [line.strip() for line in lines if 'available' in line.lower()]
    return domini_disponibili

def generate_hmac(payload: dict, secret: str) -> str:
    encoded_payload = urlencode(payload).encode('utf-8')
    return hmac.new(secret.encode('utf-8'), encoded_payload, hashlib.sha512).hexdigest()

def generate_payment_feedback(status: int, amount_crypto: float, currency: str) -> str:
    if status == 0:
        return "Payment pending. Awaiting confirmations."
    elif status < 0:
        return "Payment failed or cancelled."
    elif status >= 100:
        return f"Payment of {amount_crypto} {currency} received and confirmed."
    else:
        return "Payment status unknown."

def create_coinpayments_transaction(amount, currency, buyer_email):
    url = "https://www.coinpayments.net/api.php"
    payload = {
        'version': 1,
        'cmd': 'create_transaction',
        'amount': amount,
        'currency1': 'EUR',
        'currency2': currency,
        'buyer_email': buyer_email,
        'key': COINPAYMENTS_API_KEY,
        'format': 'json'
    }
    headers = {
        'HMAC': generate_hmac(payload, COINPAYMENTS_API_SECRET)
    }
    response = requests.post(url, headers=headers, data=payload)
    logger.info(f"Transaction creation response: {response.json()}")
    return response.json()

def get_tx_info(txn_id):
    url = "https://www.coinpayments.net/api.php"
    payload = {
        'version': 1,
        'cmd': 'get_tx_info',
        'txid': txn_id,
        'key': COINPAYMENTS_API_KEY,
        'format': 'json'
    }
    
    headers = {
        'HMAC': generate_hmac(payload, COINPAYMENTS_API_SECRET)
    }
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    
    try:
        response = session.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API call to CoinPayments: {e}")
        return {'error': str(e)}

def get_supported_currencies():
    url = "https://www.coinpayments.net/api.php"
    payload = {
        'version': 1,
        'cmd': 'rates',
        'accepted': 1,  # Only show accepted coins
        'key': COINPAYMENTS_API_KEY,
        'format': 'json'
    }
    
    headers = {
        'HMAC': generate_hmac(payload, COINPAYMENTS_API_SECRET)
    }
    
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

async def profile(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name

    user_language = user_lang.get(user_id, 'ENG')
    if user_id not in user_data:
        user_data[user_id] = {
            'credits': 0,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'free_scans_remaining': FREE_SCANS
        }

    credits = user_data[user_id]['credits'] / SCANSIONI_PER_EURO
    scans = user_data[user_id]['credits']
    free_scans_remaining = user_data[user_id]['free_scans_remaining']

    response = TEXTS[user_language]['profile_saved'].format(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        credits=credits,
        scans=scans,
        free_scans=free_scans_remaining
    )

    await update.message.reply_text(response)
    save_user_data(user_data)

def get_supported_currencies():
    url = "https://www.coinpayments.net/api.php"
    payload = {
        'version': 1,
        'cmd': 'rates',
        'accepted': 1,  # Show only accepted coins
        'key': COINPAYMENTS_API_KEY,
        'format': 'json'
    }

    headers = {
        'HMAC': generate_hmac(payload, COINPAYMENTS_API_SECRET)
    }

    response = requests.post(url, headers=headers, data=payload)
    return response.json()

currency_list = ['BTC', 'ETH', 'LTC', 'LTCT']

def generate_html_for_currencies(currency_list):
    logger.info("Generating HTML content for accepted currencies.")
    
    if not currency_list:
        logger.error("The currency list is empty!")
        return "accepted_currencies.html"
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Accepted Currencies</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 1;
                padding: 30px;
                background-color: #f9f9f9;
                color: #333;
            }
            h1 {
                color: #1C6BA2;
            }
            ul {
                list-style-type: none;
                padding: 50;
            }
            li {
                background: #ddd;
                margin: 10px 0;
                padding: 10px;
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <center><h1>💎 Accepted Cryptocurrencies of Domain scraper Bot 💎</h1></center>
        <ul>
    """
    
    logger.info(f"Currency list: {currency_list}")
    
    for currency in currency_list:
        logger.info(f"Adding currency: {currency}")
        html_content += f"<li>{currency}</li>\n"
    
    html_content += """
        </ul>
    </body>
    </html>
    """
    
    logger.info(f"HTML content generated: {html_content}")
    file_path = "accepted_currencies.html"
    
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            logger.info("Writing the HTML file.")
            file.write(html_content)
        logger.info(f"HTML content written to file: {file_path}")
    except IOError as e:
        logger.error(f"Error writing the file: {e}")
        return "accepted_currencies.html"
    
    # Verifying if file content is as written
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            read_content = file.read()
        logger.info(f"HTML content read successfully from file.")
        logger.info(f"HTML content within file: {read_content}")
    except IOError as e:
        logger.error(f"Error reading the file: {e}")
        return "accepted_currencies.html"
    
    return file_path

async def currency(update: Update, context: CallbackContext) -> None:
    logger.info("Executing /currency command.")

    currencies = ['BTC', 'ETH', 'LTC', 'BTC.BEP20', 'BCH', 'BNB', 'BUSD', 'DOGE', 'DOT.BEP20', 'ETC', 'ETC.BEP20', 'MATIC.POLY', 'SHIB', 'TRX', 'USDC', 'USDC.BEP20', 'USDT.BEP20', 'XMR', 'LTCT']
    logger.info(f"Fetched currency list: {currencies}")

    file_path = generate_html_for_currencies(currencies)
    logger.info(f"Generated file path: {file_path}")

    verify_file_content(file_path)

    if file_path and os.path.exists(file_path):
        logger.info(f"Sending file: {file_path}")
        with open(file_path, 'rb') as file_data:
            await update.message.reply_document(document=InputFile(file_data, filename="accepted_currencies.html"))

        os.remove(file_path)
        logger.info(f"File deleted: {file_path}")
    else:
        logger.error("The HTML file was not created correctly.")
        await update.message.reply_text("The HTML file was not created correctly.")

def verify_file_content(file_path):
    try:
        if not os.path.exists(file_path):
            logger.error(f"File path does not exist: {file_path}")
            return None
        
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            logger.info(f"File content being sent: {content}")
        return content
    except Exception as e:
        logger.error(f"Error verifying file content: {e}")
        return None

async def set_language(update: Update, context: CallbackContext) -> None:
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(TEXTS[user_lang.get(update.message.from_user.id, 'ENG')]['invalid_language_message'])
        return

    language = context.args[0].upper()
    if language not in ['ITA', 'ENG']:
        await update.message.reply_text(TEXTS[user_lang.get(update.message.from_user.id, 'ENG')]['invalid_language_message'])
        return

    user_id = update.message.from_user.id
    user_lang[user_id] = language

    await update.message.reply_text(TEXTS[language]['language_set'])

async def setfile_attachments(update: Update, context: CallbackContext) -> None:
    # Chiediamo all'utente di caricare un file .txt o .csv
    user_language = user_lang.get(update.message.from_user.id, 'ENG')
    response = f"📄 {TEXTS[user_language]['file_path_not_specified']}"
    await update.message.reply_text(response)

async def handle_document(update: Update, context: CallbackContext) -> None:
    user_language = user_lang.get(update.message.from_user.id, 'ENG')
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name

    # Verifica che il file abbia l'estensione corretta
    if not file_name.endswith(('.txt', '.csv')):
        await update.message.reply_text(TEXTS[user_language]['file_extension_error'])
        return

    new_file = await context.bot.get_file(file_id)
    file_path = os.path.join('uploads', file_name)
    
    # Creiamo la directory uploads se non esiste
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    await new_file.download_to_drive(file_path)

    # Salva il file caricato per l'utente
    user_files[update.message.from_user.id] = file_path
    
    response = TEXTS[user_language]['file_upload_success'].format(file_name=file_name)
    await update.message.reply_text(response)

async def pay(update: Update, context: CallbackContext) -> None:
    user_language = user_lang.get(update.message.from_user.id, 'ENG')
    
    if len(context.args) < 3:
        await update.message.reply_text(TEXTS[user_language]['payment_usage'])
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(TEXTS[user_language]['invalid_payment_amount'])
        return

    if amount < MIN_PAYMENT_AMOUNT:
        await update.message.reply_text(TEXTS[user_language]['min_payment_amount_error'].format(MIN_PAYMENT_AMOUNT=MIN_PAYMENT_AMOUNT))
        return

    currency = context.args[1]
    email = context.args[2]
    user_id = update.message.from_user.id

    response = create_coinpayments_transaction(amount, currency, email)
    if response['error'] == 'ok':
        user_payments[user_id] = response['result']
        status_message = await update.message.reply_text(TEXTS[user_language]['payment_wait_feedback'].format(status_url=response['result']['status_url']))
        # Salva l'ID del messaggio per il futuro aggiornamento
        context.job_queue.run_repeating(check_payment_status, interval=60, first=60, data={'update': update, 'user_id': user_id, 'message_id': status_message.message_id})
    else:
        await update.message.reply_text(TEXTS[user_language]['payment_error'].format(error=response['error']))

async def get_file_id(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    await update.message.reply_text(f'File ID: {file_id}')
    

def get_conversion_rate(currency_to_convert: str) -> float:
    url = "https://www.coinpayments.net/api.php"
    payload = {
        'version': 1,
        'cmd': 'rates',
        'accepted': 1,
        'key': COINPAYMENTS_API_KEY,
        'format': 'json'
    }
    headers = {
        'HMAC': generate_hmac(payload, COINPAYMENTS_API_SECRET)
    }
    response = requests.post(url, headers=headers, data=payload).json()
    logger.info(f"Rates response: {response}")  # Aggiungi un log per la risposta dei tassi
    if response['error'] == 'ok':
        rates = response['result']
        if currency_to_convert in rates and 'rate_btc' in rates[currency_to_convert]:
            rate_btc = float(rates[currency_to_convert]['rate_btc'])
            btc_to_eur = float(rates['EUR']['rate_btc'])
            logger.info(f"rate_btc for {currency_to_convert}: {rate_btc}")  # Log per il tasso BTC dell'altra valuta
            logger.info(f"btc_to_eur rate: {btc_to_eur}")  # Log per il tasso BTC-EUR
            everything_to_eur = rate_btc / btc_to_eur  # Fai attenzione a questo calcolo, potrebbe essere invertito
            logger.info(f"Conversion rate for {currency_to_convert} to EUR: {everything_to_eur}")  # Log per il tasso finale
            return everything_to_eur
    else:
        raise ValueError(f"Error fetching rates: {response['error']}")

async def check_payment_status(context: CallbackContext):
    job_data = context.job.data
    update = job_data['update']
    user_id = job_data['user_id']
    message_id = job_data['message_id']
    user_language = user_lang.get(user_id, 'ENG')
    payment = user_payments.get(user_id, {})

    response = get_tx_info(payment.get('txn_id'))
    logger.info(f"Transaction status response for txn {payment.get('txn_id')}: {response}")

    if response.get('error') and response['error'] != 'ok':
        logger.error(f"Payment check failed: {response['error']}")
        await context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=message_id, text=TEXTS[user_language]['payment_error'].format(error=response['error']))
        context.job.schedule_removal()
        return

    if response['error'] == 'ok':
        status = response['result']['status']
        amount_paid_crypto = float(response['result']['receivedf'])
        currency = response['result']['coin']

        feedback = generate_payment_feedback(status, amount_paid_crypto, currency)
        text_to_send = TEXTS[user_language]['payment_pending']
        if status >= 0 and status < 100:
            text_to_send = TEXTS[user_language]['payment_pending']
        elif status >= 100:
            try:
                rate_eur = get_conversion_rate(currency)
                amount_paid_eur = amount_paid_crypto * rate_eur

                # Log per debugging del tasso di conversione e del calcolo
                logger.info(f"Currency {currency} to BTC rate is {rate_eur}")
                logger.info(f"Transaction complete: {amount_paid_crypto} {currency} converted to {amount_paid_eur} €")

                scansioni_acquistate = int(amount_paid_eur * SCANSIONI_PER_EURO)
                
                # Logging prima dell'aggiornamento dei crediti
                current_credits = user_credits.get(user_id, 0)
                logger.info(f"Current credits for user {user_id}: {current_credits}. New scans purchased: {scansioni_acquistate}")

                # Aggiorna i crediti dell'utente
                user_credits[user_id] = current_credits + scansioni_acquistate

                # Logging dopo l'aggiornamento dei crediti
                updated_credits = user_credits[user_id]
                logger.info(f"Updated credits for user {user_id}: {updated_credits}")

                # Salva i dati aggiornati su CSV
                user_data[user_id]['credits'] = user_credits[user_id]
                save_user_data(user_data)

                text_to_send = TEXTS[user_language]['payment_successful'].format(scans=scansioni_acquistate)
                context.job.schedule_removal()
            except ValueError as e:
                logger.error(f"Error in processing payment: {str(e)}")
                text_to_send = TEXTS[user_language]['payment_error'].format(error=str(e))
                context.job.schedule_removal()
        else:
            text_to_send = TEXTS[user_language]['payment_status_unknown']

        await context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=message_id, text=text_to_send)

async def credit(update: Update, context: CallbackContext) -> None:
    logger.info("Esecuzione del comando /credit")
    user_id = update.message.from_user.id

    logger.info(f"ID Utente: {user_id} - Verifica dei crediti")

    try:
        user_language = user_lang.get(user_id, 'ENG')
        scansioni = user_credits.get(user_id, 0)
        message = TEXTS[user_language]['credit_message'].format(credit=scansioni / SCANSIONI_PER_EURO, scans=scansioni)
        await update.message.reply_text(message)
        logger.info(f"ID Utente: {user_id} - Crediti recuperati con successo")
    except Exception as e:
        logger.error(f"Errore nella verifica dei crediti per l'utente {user_id}: {str(e)}")
        await update.message.reply_text("Si è verificato un errore durante la verifica dei crediti. Riprova più tardi.")

async def domain_command(update: Update, context: CallbackContext) -> None:
    global custom_domain_extension
    user_id = update.message.from_user.id
    user_language = user_lang.get(user_id, 'ENG')

    if context.args:
        custom_domain_extension = context.args[0]
        message = TEXTS[user_language]['domain_set_success'].format(extension=custom_domain_extension)
        await update.message.reply_text(message)
    else:
        message = TEXTS[user_language]['domain_set_error']
        await update.message.reply_text(message)

async def send_available_domains(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_language = user_lang.get(user_id, 'ENG')  # Ottieni la lingua dell'utente, predefinito a 'ENG'

    if user_id in user_files:
        file_path = user_files[user_id]
        domini_disponibili = leggi_domini_disponibili(file_path)
        if domini_disponibili:
            response = TEXTS[user_language]['available_domains'].format(domains='\n'.join(domini_disponibili))
        else:
            response = TEXTS[user_language]['no_domains_found']
    else:
        response = TEXTS[user_language]['no_file_specified']

    await update.message.reply_text(response)

async def set_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_language = user_lang.get(user_id, 'ENG')  # Ottieni la lingua dell'utente, predefinito a 'ENG'

    if context.args:
        file_path = context.args[0]
        if os.path.exists(file_path):
            user_files[user_id] = file_path
            response = TEXTS[user_language]['file_set_success'].format(file_path=file_path)
        else:
            response = TEXTS[user_language]['file_not_exist'].format(file_path=file_path)
    else:
        response = TEXTS[user_language]['file_path_not_specified']

    await update.message.reply_text(response)

async def analyze_domains(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_language = user_lang.get(user_id, 'ENG')

    if user_id in user_tasks:
        response = TEXTS[user_language]['analysis_in_progress']
        await update.message.reply_text(response)
        return

    if user_id not in user_files or not custom_domain_extension:
        response = TEXTS[user_language]['file_and_extension_not_set']
        await update.message.reply_text(response)
        return

    total_scans_remaining = user_data[user_id]['credits'] + user_data[user_id]['free_scans_remaining']

    if total_scans_remaining < 1:
        response = TEXTS[user_language]['payment_required']
        await update.message.reply_text(response)
        return

    analysis_interrupted = False
    try:
        async def analyze():
            nonlocal analysis_interrupted
            file_path = user_files[user_id]
            domini = leggiparoleconcom(file_path)
            analysis_message = await update.message.reply_text(TEXTS[user_language]['domain_analysis_start'])

            available_domains = []
            unavailable_domains = []

            try:
                for i, dominio in enumerate(domini):
                    total_scans_remaining = user_data[user_id]['credits'] + user_data[user_id]['free_scans_remaining']

                    if total_scans_remaining <= 0:
                        response = TEXTS[user_language]['scan_limit_reached']
                        await analysis_message.edit_text(response)
                        break

                    risultato = check_domain_availability(dominio)
                    if risultato == "AVAILABLE DOMAIN":
                        available_domains.append(dominio)
                    else:
                        unavailable_domains.append(f"{dominio} - {json.dumps(risultato)}")

                    if user_data[user_id]['free_scans_remaining'] > 0:
                        user_data[user_id]['free_scans_remaining'] -= 1
                        if user_data[user_id]['free_scans_remaining'] == 0:
                            await update.message.reply_text(TEXTS[user_language]['free_scan_finished'])
                    else:
                        user_data[user_id]['credits'] -= 1

                    if (i + 1) % 10 == 0 or i == len(domini) - 1:
                        progress = TEXTS[user_language]['domain_analysis_progress'].format(current=i + 1, total=len(domini))
                        await analysis_message.edit_text(progress)

                    await asyncio.sleep(1)

                await analysis_message.edit_text(TEXTS[user_language]['domain_analysis_complete'])
                
            except asyncio.CancelledError:
                analysis_interrupted = True
            finally:
                await generate_html_file(user_id, username, available_domains, unavailable_domains)
                save_user_data(user_data)

                if analysis_interrupted:
                    await update.message.reply_text(TEXTS[user_language]['analysis_stopped'])
                await update.message.reply_text(TEXTS[user_language]['domain_analysis_html_ready'])

                user_tasks.pop(user_id, None)

        user_tasks[user_id] = asyncio.create_task(analyze())
        
    except Exception as e:
        error_message = TEXTS[user_language]['domain_analysis_error'].format(error=str(e))
        await update.message.reply_text(error_message)

async def stop_analysis(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_language = user_lang.get(user_id, 'ENG')

    if user_id in user_tasks:
        task = user_tasks[user_id]
        if not task.done():  # Check if the task is still running
            task.cancel()
            await task  # Wait for the task to be canceled
            del user_tasks[user_id]

            # If there are results for the user, generate HTML file here
            # Example: html_file_path = await generate_html_file(user_id, username, available_domains, unavailable_domains)

            response = TEXTS[user_language]['analysis_stopped']
            await update.message.reply_text(response)
        else:
            response = TEXTS[user_language]['no_analysis_in_progress']
            await update.message.reply_text(response)
    else:
        response = TEXTS[user_language]['no_analysis_in_progress']
        await update.message.reply_text(response)

async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg='Exception while handling an update:', exc_info=context.error)

async def generate_html_file(user_id, username, available_domains, unavailable_domains):
    global scheduler
    user_language = user_lang.get(user_id, 'ENG')

    if not available_domains and not unavailable_domains:
        return

    html_content = f"""
    <!DOCTYPE html>
    <html lang="{user_language.lower()}">
    <head>
        <meta charset="UTF-8">
        <title>{TEXTS[user_language]['html_title']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; padding: 20px; background-color: #f9f9f9; color: #333; }}
            .comprabile {{ color: green; font-weight: bold; }}
            .in-uso {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>{TEXTS[user_language]['html_header']}</h1>
        <h2>{TEXTS[user_language]['html_comprabili']}</h2>
        <ul>
    """

    for domain in available_domains:
        html_content += f"<li class='comprabile'>{domain}</li>"

    html_content += f"""
        </ul>
        <h2>{TEXTS[user_language]['html_in_uso']}</h2>
        <ul>
    """

    for domain in unavailable_domains:
        html_content += f"<li class='in-uso'>{domain}</li>"

    html_content += f"""
        </ul>
        <p>{TEXTS[user_language]['restart_bot_message']}</p>
    </body>
    </html>
    """

    file_path = f"results_{username}.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    # Genera un ID unico per il job
    job_id = f"delete_{username}_html_{int(time.time())}"

    # Pianifica l'eliminazione del file tra 30 minuti
    scheduler.add_job(
        delete_file, 
        'date', 
        run_date=datetime.now() + timedelta(minutes=30), 
        args=[file_path],
        id=job_id
    )

    return file_path
    
async def list_domains(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username
    user_id = update.message.from_user.id
    user_language = user_lang.get(user_id, 'ENG')
    file_path = f"results_{username}.html"
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                await update.message.reply_document(
                    document=InputFile(file, filename=file_path),
                    caption=TEXTS[user_language]['restart_bot_message']
                )
        else:
            response = TEXTS[user_language]['no_domains_analyzed']
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Errore durante l'invio del file: {str(e)}")
        error_message = TEXTS[user_language]['timeout_error']
        await update.message.reply_text(error_message)

    except httpx.ReadTimeout:
        # Gestione dell'errore di timeout
        error_message = TEXTS[user_language]['timeout_error']
        await update.message.reply_text(error_message)

async def supported_domains(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    language = user_lang.get(user_id, 'ENG')  # Prendi la lingua dell'utente, predefinita a 'ENG'

    supp_TLDs_text = TEXTS[language]['supp_TLDs']

    await update.message.reply_text(supp_TLDs_text)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user if update.message else update.callback_query.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    language = user_lang.get(user_id, 'ENG')

    # Imposta l'immagine di benvenuto (usa il tuo file_id ottenuto precedentemente)
    photo_file_id = 'C:\\Users\\OMEN\\Desktop\\domain.jpg'

    # Inizializza la lingua impostata se non presente
    if user_id not in user_lang:
        user_lang[user_id] = 'ENG'  # Default to English

    # Inizializza i dati dell'utente se non presenti
    if user_id not in user_data:
        user_data[user_id] = {
            'credits': 0,
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }

    # Aggiorna i dati dell'utente
    user_data[user_id].update({'username': username, 'first_name': first_name, 'last_name': last_name})
    save_user_data(user_data)

    # Invia l'immagine di benvenuto
    await context.bot.send_photo(
        chat_id=update.message.chat_id if update.message else update.callback_query.message.chat_id,
        photo=photo_file_id,
    )

    # Invia il messaggio di benvenuto
    welcome_message = TEXTS[language]['welcome_message']
    await context.bot.send_message(
        chat_id=update.message.chat_id if update.message else update.callback_query.message.chat_id,
        text=welcome_message
    )

from apscheduler.schedulers.asyncio import AsyncIOScheduler

def main():
    global scheduler
    delete_webhook()
    application = Application.builder().token(TOKEN).build()
    scheduler = AsyncIOScheduler()
    application.job_queue.scheduler = scheduler
    scheduler.start()
    update = Update(...)
    context = CallbackContext(...)
    list_domains(update, context)

    global user_data, user_credits, user_profiles
    user_data = load_user_data()
    user_credits = {user_id: data['credits'] for user_id, data in user_data.items()}

    application.add_handler(CommandHandler("lang", set_language))
    application.add_handler(CommandHandler("available", send_available_domains))
    application.add_handler(CommandHandler("setfile", set_file))
    application.add_handler(CommandHandler("analyze", analyze_domains))
    application.add_handler(CommandHandler("stop", stop_analysis))
    application.add_handler(CommandHandler("list", list_domains))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("domain", domain_command))
    application.add_handler(CommandHandler("credit", credit))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("pay", pay))
    application.add_handler(CommandHandler("currency", currency))
    application.add_handler(CommandHandler("supported", supported_domains))
    application.add_handler(CommandHandler("wordlist", wordlist))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.PHOTO, get_file_id))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == "__main__":
    main()