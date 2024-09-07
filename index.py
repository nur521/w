import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

API_TOKEN = '7254708854:AAEop3TvQaazXTo8ZWx7djq8jBy1PMo4w-Q'
CHANNEL_ID = '-1002181122538'
BOT_NICKNAME = 'Practice_app_bot'
TOTAL_SUPPLY = 100_000_000_000  # 100 миллиардов токенов

bot = telebot.TeleBot(API_TOKEN)

# Создаем или подключаемся к базе данных SQLite
conn = sqlite3.connect('tokens.db', check_same_thread=False)
cursor = conn.cursor()
# Создаем таблицы, если они еще не созданы
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    tokens INTEGER DEFAULT 0,
    referred_by INTEGER,
    referral_count INTEGER DEFAULT 0,
    received_initial_tokens BOOLEAN DEFAULT 0,
    wallet_address TEXT
)''')
conn.commit()

def create_markup(include_menu=False, include_balance=False):
    """Создаем клавиатуру с кнопками. Кнопка Menu добавляется только если include_menu=True, Balance — если include_balance=True."""
    markup = InlineKeyboardMarkup()
    subscribe_button = InlineKeyboardButton("Subscribe", url="https://t.me/nuriknik")
    
    if not include_menu:  # Включаем кнопку Check только до нажатия Menu
        check_button = InlineKeyboardButton("Check", callback_data="check")
        markup.add(subscribe_button, check_button)
    else:
        markup.add(subscribe_button)
    
    if include_balance:
        balance_button = InlineKeyboardButton("Balance", callback_data="balance")
        markup.add(balance_button)
    
    if include_menu:
        menu_button = InlineKeyboardButton("Menu", callback_data="menu")
        referral_button = InlineKeyboardButton("Show Referral", callback_data="show_referral")
        referral_link_button = InlineKeyboardButton("Referral Link", callback_data="referral_link")
        all_tokens_button = InlineKeyboardButton("All Tokens", callback_data="all_tokens")
        markup.add(menu_button, referral_button, referral_link_button, all_tokens_button)
    
    return markup

# Функция для расчета оставшихся токенов
def get_remaining_tokens():
    cursor.execute("SELECT SUM(tokens) FROM users")
    used_tokens = cursor.fetchone()[0] or 0
    remaining_tokens = TOTAL_SUPPLY - used_tokens
    return remaining_tokens

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, есть ли пользователь в базе данных, если нет - добавляем
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referrer_id = message.text.split()[-1] if len(message.text.split()) > 1 else None
        cursor.execute("INSERT INTO users (user_id, username, tokens, referred_by, received_initial_tokens) VALUES (?, ?, 0, ?, 0)", 
                       (user_id, username, referrer_id))
        conn.commit()

        # Обновляем количество рефералов у реферера и добавляем токены
        if referrer_id:
            cursor.execute("SELECT referral_count, tokens FROM users WHERE user_id = ?", (referrer_id,))
            referrer = cursor.fetchone()
            if referrer:
                if referrer[0] < 5:  # Даем токены только до 5 рефералов
                    new_referral_count = referrer[0] + 1
                    new_tokens = referrer[1] + 50  # Добавляем 50 токенов за реферала
                    cursor.execute("UPDATE users SET referral_count = ?, tokens = ? WHERE user_id = ?", 
                                   (new_referral_count, new_tokens, referrer_id))
                    conn.commit()

    markup = create_markup()  # Только Subscribe и Check
    bot.send_message(message.chat.id, "Hi! Please subscribe to our channel and click /check to check, then, receive tokens.", reply_markup=markup)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "check":
        markup = create_markup(include_menu=True)  # После проверки добавляем Menu и убираем Check
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Проверяем, получал ли пользователь уже 5000 токенов за подписку
            cursor.execute("SELECT received_initial_tokens, tokens, referral_count FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            received_initial_tokens = user_data[0]
            user_tokens = user_data[1]
            referral_count = user_data[2]
            remaining_tokens = get_remaining_tokens()
            
            if not received_initial_tokens:
                cursor.execute("UPDATE users SET tokens = tokens + 5000, received_initial_tokens = 1 WHERE user_id = ?", (user_id,))
                conn.commit()

                # Формируем ссылку с параметрами для передачи на Web App
                web_app_url = f"https://nur521.github.io/t/?username={call.from_user.username}&user_id={user_id}&balance={user_tokens + 5000}&remaining_tokens={remaining_tokens}&referrals={referral_count}"

                # Кнопка Open Web App
                web_app_markup = InlineKeyboardMarkup()
                web_app_button = InlineKeyboardButton("Open Web App", url=web_app_url)
                web_app_markup.add(web_app_button)

                bot.send_message(call.message.chat.id, "Great! You are subscribed. Open the web app below:", reply_markup=web_app_markup)

                # После кнопки Web App выводим сообщение о токенах
                bot.send_message(call.message.chat.id, "You earned 5000 MineCoins.\n\nUse the menu below:", reply_markup=markup)
            else:
                web_app_url = f"https://nur521.github.io/t/?username={call.from_user.username}&user_id={user_id}&balance={user_tokens}&remaining_tokens={remaining_tokens}&referrals={referral_count}"

                web_app_markup = InlineKeyboardMarkup()
                web_app_button = InlineKeyboardButton("Open Web App", url=web_app_url)
                web_app_markup.add(web_app_button)
                bot.send_message(call.message.chat.id, "Great! You are subscribed. Open the web app below:", reply_markup=web_app_markup)
                bot.send_message(call.message.chat.id, "You have already received your 5000 tokens.\n\nUse the menu below:", reply_markup=markup)
                
        else:
            bot.send_message(call.message.chat.id, "You are not subscribed to the channel. Please subscribe and try again.\n\nUse the menu below:", reply_markup=markup)
    
    elif call.data == "balance":
        cursor.execute("SELECT tokens FROM users WHERE user_id = ?", (user_id,))
        tokens = cursor.fetchone()[0]
        markup = create_markup(include_menu=True, include_balance=True)
        bot.send_message(call.message.chat.id, f"You have {tokens} MineCoins.\n\nUse the menu below:", reply_markup=markup)
    
    elif call.data == "menu":
        markup = create_markup(include_menu=True, include_balance=True)
        username = call.from_user.username
        bot.send_message(call.message.chat.id, f"Hi {username}. Welcome to MineCoin!\n\nUse the menu below:", reply_markup=markup)

    elif call.data == "show_referral":
        # Получаем список рефералов
        cursor.execute("SELECT user_id, username FROM users WHERE referred_by = ?", (user_id,))
        referrals = cursor.fetchall()
        
        if referrals:
            referral_list = "\n".join([f"UserID: {r[0]}, Username: @{r[1]}" for r in referrals])
            bot.send_message(call.message.chat.id, f"Your referrals:\n{referral_list}\n\nUse the menu below:")
        else:
            bot.send_message(call.message.chat.id, "You have no referrals.\n\nUse the menu below:")

    elif call.data == "referral_link":
        # Генерируем реферальную ссылку
        markup = create_markup(include_menu=True, include_balance=True)
        bot.send_message(call.message.chat.id, f"Your referral link: https://t.me/{BOT_NICKNAME}?start={user_id}\n\nUse the menu below:", reply_markup=markup)

    elif call.data == "all_tokens":
        remaining_tokens = get_remaining_tokens()
        bot.send_message(call.message.chat.id, f"Total tokens remaining: {remaining_tokens} MineCoins.\n\nUse the menu below:")

bot.infinity_polling()
