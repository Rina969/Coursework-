from gettext import textdomain

import telebot
from telebot import types
import sqlite3

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

#======================
#====HEAD OF STUDIO====
#======================
from telegram import Update
from telegram.ext import CallbackContext


def show_main_menu(markup):
    btn1 = types.KeyboardButton('Статистика')
    btn2=types.KeyboardButton('Новые заявки')
    markup.row(btn1, btn2)
    btn3 = types.KeyboardButton('Изменить информацию о студии')


def head_start(message):
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

@bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
# ====================
# РЕДАКТИРОВАНИЕ СТУДИИ
# ====================

@bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
def edit_info(message):
    """
    Обработчик кнопки 'Изменить информацию о студии'.
    Начинает процесс пошагового редактирования студии.
    """
    user_id = message.from_user.id

    # Начинаем процесс редактирования через наш класс StudioEditor
    response = studio_editor.start_editing(user_id)

    # Отправляем первое сообщение с инструкцией
    bot.send_message(
        message.chat.id,
        response,
        parse_mode='html'
    )


@bot.message_handler(func=lambda message: studio_editor.get_user_step(message.from_user.id) in
                                          ['waiting_for_name', 'waiting_for_description'])
def handle_text_for_editing(message):
    """
    Обработчик текстовых сообщений во время редактирования студии.

    Этот обработчик срабатывает ТОЛЬКО когда пользователь находится
    на этапе 'waiting_for_name' или 'waiting_for_description'.
    """
    user_id = message.from_user.id

    # Передаем текст сообщения в редактор студии
    response, is_completed = studio_editor.handle_message(user_id, message.text)

    # Отправляем ответ пользователю
    bot.send_message(
        message.chat.id,
        response,
        parse_mode='html'
    )

    # Если процесс редактирования завершен, показываем главное меню
    if is_completed:
        # Показываем кнопки для дальнейших действий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        show_main_menu(markup)

        bot.send_message(
            message.chat.id,
            "Что дальше?",
            reply_markup=markup
        )


@bot.message_handler(content_types=['photo'])
def handle_photo_for_editing(message):
    """
    Обработчик фото во время редактирования студии.

    Этот обработчик срабатывает, когда пользователь отправляет фото.
    Проверяем, находится ли пользователь на этапе ожидания изображения.
    """
    user_id = message.from_user.id

    # Проверяем, находится ли пользователь на этапе ожидания изображения
    if studio_editor.get_user_step(user_id) != 'waiting_for_image':
        # Если нет - игнорируем фото или сообщаем об ошибке
        return

    # Получаем информацию о самом большом фото (Telegram отправляет несколько размеров)
    file_id = message.photo[-1].file_id

    # Скачиваем фото с серверов Telegram
    file_info = bot.get_file(file_id)
    image_bytes = bot.download_file(file_info.file_path)

    # Передаем изображение в редактор студии
    response, is_completed = studio_editor.handle_image(user_id, image_bytes)

    # Отправляем ответ пользователю
    bot.send_message(
        message.chat.id,
        response,
        parse_mode='html'
    )


@bot.message_handler(commands=['cancel'])
def cancel_editing(message):
    """
    Обработчик команды /cancel для отмены редактирования.
    """
    user_id = message.from_user.id
    response = studio_editor.cancel_editing(user_id)

    # Возвращаем в главное меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    show_main_menu(markup)

    bot.send_message(
        message.chat.id,
        response,
        parse_mode='html',
        reply_markup=markup
    )


