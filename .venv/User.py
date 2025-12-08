from gettext import textdomain

import telebot
from telebot import types
import sqlite3

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

#======================
#=========USER=========
#======================


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Каталог студий')
    markup.row(btn1)
    btn2=types.KeyboardButton('Мои заявки')
    btn3 = types.KeyboardButton('Главное меню')
    markup.row(btn2, btn3)

    bot.send_message(message.chat.id,
                     f'<em>Привет, {message.from_user.first_name}, в этом боте ты можешь узнать про творческие студии'
                     f' ГУАП и стать частью активной студенческой жизни!</em>', parse_mode='html', reply_markup=markup)

# ДАЛЕЕ ВЕТКА : КАТАЛОГ СТУДИЙ

@bot.message_handler(func=lambda message: message.text == 'Каталог студий')
def inline_button_catalog(message):
    markup = types.InlineKeyboardMarkup()
    btn_orgmero = types.InlineKeyboardButton("Студия организации мероприятий", callback_data='orgMero')
    markup.row(btn_orgmero)
    btn_tehguap = types.InlineKeyboardButton("Студия технического обеспечения мероприятий", callback_data='tehGuap')
    markup.row(btn_tehguap)
    btn_muzguap = types.InlineKeyboardButton("МУЗГУАП", callback_data='muzGuap')
    markup.row(btn_muzguap)
    btn_dance = types.InlineKeyboardButton("Танцевальная студия", callback_data='dance')
    markup.row(btn_dance)
    btn_theatr= types.InlineKeyboardButton("Театральная студия", callback_data='theatr')
    markup.row(btn_theatr)
    btn_comedy = types.InlineKeyboardButton("КВН", callback_data='comedy')
    markup.row(btn_comedy)
    btn_vedush = types.InlineKeyboardButton("Студия ведущих", callback_data='vedush')
    markup.row(btn_vedush)
    btn_media =  types.InlineKeyboardButton("Медиацентр", callback_data='media')
    markup.row(btn_media)

    bot.send_message(message.chat.id, 'Нажми на студию для просмотра:', reply_markup=markup)

# @bot.callback_query_handler(func=lambda callback: callback.data == 'orgMero')
# def orgMeroInfo(callback):

# ДАЛЕЕ ВЕТКА : МОИ ЗАЯВКИ

@bot.message_handler(func=lambda message: message.text == 'Мои заявки')
def membership_appl(message):
    bot.send_message(message.chat.id, 'Вот статус твоих заявок:')


#Данные пользователя (для себя сделала)
@bot.message_handler(commands=['user'])
def main(message):

    text=message
    if not isinstance(text, str):
        text = str(text)

    message_parts = split_message(text)

    # Отправляем каждую часть отдельным сообщением
    for part in message_parts:
        bot.send_message(message.chat.id, part)


def split_message(text, max_length=4096):
    """Разделяет текст на части не превышающие max_length"""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]


# @bot.message_handler(content_types=['photo'])
# def get_photo(message):
#     markup = types.InlineKeyboardMarkup()
#     btn1 = types.InlineKeyboardButton('Duuuuura', url='https://t.me/+lVcKrLQJxH9hODYy')
#     markup.row(btn1)
#     btn2 = types.InlineKeyboardButton('Удалить фото!', callback_data='delete')
#     btn3 = types.InlineKeyboardButton('Изменить', callback_data='edit')
#     markup.row(btn2,btn3)
#
#     bot.reply_to(message, "Спасибо, подрочил", reply_markup = markup)
#
# @bot.callback_query_handler(func=lambda callback:True)
# def callback_message(callback):
#     if callback.data == 'delete':
#         bot.delete_message(callback.message.chat.id, callback.message.message_id-1)
#     elif callback.data == 'edit':
#         bot.edit_message_text('Падем выдим', callback.message.chat.id, callback.message.message_id)
#
#
#
#
# def on_click(message):
#     if message.text.lower == 'вступить в табор':
#         bot.send_message(message.chat.id, 'Добро пожаловать к дурам, тварина')
#     elif message.text.lower == 'аборт':
#         bot.send_message(message.chat.id, 'Ну удалил и чо')
#
#
#


bot.polling(none_stop=True)