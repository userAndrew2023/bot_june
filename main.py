import os
from datetime import datetime

import telebot
from telebot import types
import sqlite3
import pandas as pd
from telebot.types import CallbackQuery

conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS subscribers
                  (user_id INTEGER PRIMARY KEY, username TEXT)''')
conn.commit()

bot = telebot.TeleBot('7206503391:AAGZgZU4jsEAcCLbxIWpvZUZlyqdUBeKD08')


@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute("SELECT COUNT(*) FROM subscribers")
    count = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup()
    subscribe_button = types.InlineKeyboardButton(f"Участвовать ({count})", callback_data="check_sub")
    markup.add(subscribe_button)
    bot.send_message(message.chat.id, """<b>😍 Музыка, а не розыгрыш!</b>
Разыгрываем одни наушники Apple Airpods!
Для участия необходимо подписаться на наш канал @vamdodomaru и нажать кнопку "Участвовать" под этим постом.

Итоги подведем 11 июня в 14:00 случайным образом с помощью рандомайзера. Приз отправим в любой город России и СНГ, доставка за наш счет! 🔥""",
                     reply_markup=markup, parse_mode="HTML")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_subscription(message):
    if message.text == "/excel":
        generate_excel(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub(call: CallbackQuery):
    user_id = call.from_user.id
    if (cursor.execute(f"SELECT * FROM subscribers WHERE user_id = '{user_id}'").fetchone()):
        bot.send_message(call.from_user.id, "Вы уже учавствуете в конкурсе")
    elif check_if_subscribed(user_id, "@vamdodomaru"):
        add_to_database(user_id, call.from_user.username)
        bot.send_message(call.from_user.id, "Вы учавствуете в конкурсе 🔥")
    else:
        bot.send_message(call.from_user.id, "Пожалуйста, подпишитесь на канал для участия.")
    bot.answer_callback_query(call.id)


def check_if_subscribed(user_id, channel_username):
    try:
        chat_member = bot.get_chat_member(channel_username, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except Exception as e:
        print("Error occurred: ", e)
        return False


def add_to_database(user_id, username=None):
    cursor.execute("INSERT INTO subscribers (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()


def generate_excel(chat_id):
    cursor.execute("SELECT * FROM subscribers WHERE username IS NOT NULL")
    now = datetime.now()
    formatted_time = now.strftime("%S%M%H")
    data = cursor.fetchall()
    data = list(map(lambda sublist: list(map(str, sublist)), data))
    filename = f"subscribers_{formatted_time}.xlsx"
    df = pd.DataFrame(data, columns=['User ID', 'Username'])
    df.to_excel(filename, index=False)
    with open(filename, "rb") as file:
        bot.send_document(chat_id=chat_id, document=file)
    os.remove(filename)


if __name__ == '__main__':
    bot.infinity_polling()
