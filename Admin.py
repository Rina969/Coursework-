from gettext import textdomain

import telebot
from telebot import types
import uuid             # Для генерации уникальных имен файлов
from datetime import datetime  # Для работы с датами и временем
import sqlite3

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

#======================
#========ADMIN=========
#======================


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Статистика')
    btn2=types.KeyboardButton('Рассылка')
    btn3 = types.KeyboardButton('Назначить администратора')
    markup.row(btn1,btn2,btn3)
    btn4 = types.KeyboardButton('Изменить информацию о студиях')
    markup.row(btn4)

    bot.send_message(message.chat.id,
                     f'<em> Добро пожаловать, {message.from_user.first_name}.</em>', parse_mode='html', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Статистика')
def stat(message):
        bot.send_message(message.chat.id,
                    f'<em>Статистика активности:</em>', parse_mode='html')

@bot.message_handler(func=lambda message: message.text == 'Рассылка')
def stat(message):
        bot.send_message(message.chat.id,
                    f'<em>Введите сообщение:</em>', parse_mode='html')

@bot.message_handler(func=lambda message: message.text == 'Назначить администратора')
def give_role(message):
    bot.send_message(message.chat.id,
                    f'<em>Кого вы хотите назначить?</em>', parse_mode='html')
    # Регистрируем следующий шаг для получения username
    bot.register_next_step_handler(message, get_admin_username)


def get_admin_username(message):
    # Если пользователь переслал сообщение
    if message.forward_from:
        admin_username = f"@{message.forward_from.username}" if message.forward_from.username else str(
            message.forward_from.id)
        bot.send_message(message.chat.id, f"Username: {admin_username}")

    # Если ввели текст с @
    elif message.text and '@' in message.text:
        admin_username = message.text
        bot.send_message(message.chat.id, f"Username получен: {admin_username}")




bot.polling(none_stop=True)