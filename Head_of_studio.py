from gettext import textdomain

import telebot
from telebot import types
import sqlite3

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

#======================
#====HEAD OF STUDIO====
#======================
def show_main_menu(markup):
    btn1 = types.KeyboardButton('Статистика')
    btn2=types.KeyboardButton('Новые заявки')
    markup.row(btn1, btn2)
    btn3 = types.KeyboardButton('Изменить информацию о студии')


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    show_main_menu(markup)

    bot.send_message(message.chat.id,
                     f'<em>Добро пожаловать, {message.from_user.first_name}.</em>', parse_mode='html',
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Главное меню')
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    show_main_menu(markup)

    bot.send_message(message.chat.id,
                     f'<em>Вы вернулись в меню.</em>', parse_mode='html',
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Статистика')
def stat(message):
    bot.send_message(message.chat.id,
                     f'<em>Статистика подачи заявок в студию</em>', parse_mode='html')

@bot.message_handler(func=lambda message: message.text == 'Новые заявки')
def appls(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_accept = types.KeyboardButton ('❤️-Принять')
    btn_refuse = types.KeyboardButton ('Отклонить')
    btn_communicate = types.KeyboardButton ('💬-Связаться')
    markup.row(btn_accept, btn_communicate, btn_refuse)
    btn_menu=(types.KeyboardButton('Главное меню'))
    markup.row(btn_menu)

    bot.send_message(message.chat.id,
                     f'<em>Просмотр заявок:</em>', parse_mode='html', reply_markup=markup)


# ---------------------------ИЗМЕНЕНИЕ ИНФОРМАЦИИ О СТУДИИ---------------------------
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    """
    Обрабатываем фото от пользователя.
    """

    # Шаг 1: Получаем file_id самого большого фото
    file_id = message.photo[-1].file_id

    # Шаг 2: Скачиваем фото с серверов Telegram
    file_info = bot.get_file(file_id)
    downloaded = bot.download_file(file_info.file_path)

@bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
def edit_info(message):

class StudioCreationStates(StatesGroup):
"""
        Класс состояний для создания студии.
        Наследуется от StatesGroup - специального класса из telebot для FSM.

        Каждое состояние - это шаг в диалоге с пользователем.
        Порядок объявления важен для логики работы.
        """
        name = State()  # Шаг 1: Ожидаем название студии
        promo_type = State()  # Шаг 2: Ожидаем выбор типа промокода
        promo_content = State()  # Шаг 3: Ожидаем сам промокод (текст или файл)
        description = State()  # Шаг 4: Ожидаем описание студии

        bot.send_message(message.chat.id, 'Введите название студии')
        studio_name =
        studio_promo =
        studio_description =


bot.polling(none_stop=True)