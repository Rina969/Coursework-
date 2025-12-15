from gettext import textdomain

from telegram import Update
from telegram.ext import CallbackContext
import telebot
from telebot import types
import uuid             # Для генерации уникальных имен файлов
from datetime import datetime  # Для работы с датами и временем
import sqlite3 as sq
import os

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

def get_connection():
    # Путь к вашей базе данных
    db_path = os.path.join(os.path.dirname(__file__), 'student_studios_bot (1).db')
    conn = sq.connect(db_path)
    return conn
#======================
#========ADMIN=========
#======================

@bot.message_handler(commands=['start'])
def admin_start(message):
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
                     "Перешлите сообщение пользователя или введите @username")
    bot.register_next_step_handler(message, get_admin_username)


def get_admin_username(message):
    # Получаем username
    admin_username = None

    if message.forward_from:
        if message.forward_from.username:
            admin_username = f"@{message.forward_from.username}"
        else:
            admin_username = str(message.forward_from.id)
        bot.send_message(message.chat.id, f"Username: {admin_username}")

    elif message.text and '@' in message.text:
        admin_username = message.text
        bot.send_message(message.chat.id, f"Username получен: {admin_username}")

    else:
        bot.send_message(message.chat.id, "Ошибка! Введите @username или перешлите сообщение")
        return

    # Проверяем, существует ли пользователь в базе
    user_exists, existing_name, existing_phone = check_user_exists(admin_username)

    if user_exists:
        # Если пользователь существует, используем сохраненные данные
        save_admin_to_db(admin_username, existing_name, existing_phone, message.chat.id)
        return

    # Если пользователь не существует, запрашиваем ФИО
    bot.send_message(message.chat.id, "Теперь введите ФИО нового администратора:")
    bot.register_next_step_handler(message, get_admin_name, admin_username)


def get_admin_name(message, admin_username):
    # Получаем ФИО
    admin_name = message.text

    if not admin_name or len(admin_name) < 2:
        bot.send_message(message.chat.id, "ФИО должно быть не короче 2 символов")
        return

    bot.send_message(message.chat.id, f"ФИО: {admin_name}")

    # Запрашиваем номер телефона
    bot.send_message(message.chat.id, "Теперь введите номер телефона администратора (например, +79123456789):")
    bot.register_next_step_handler(message, get_admin_phone, admin_username, admin_name)


def get_admin_phone(message, admin_username, admin_name):
    # Получаем номер телефона
    admin_phone = message.text

    # Простая валидация номера телефона
    if not admin_phone or len(admin_phone) < 5:
        bot.send_message(message.chat.id, "Номер телефона должен быть не короче 5 символов")
        return

    bot.send_message(message.chat.id, f"Номер телефона: {admin_phone}")

    # Сохраняем в базу данных
    save_admin_to_db(admin_username, admin_name, admin_phone, message.chat.id)


def check_user_exists(username):
    """Проверяет, существует ли пользователь в базе и возвращает его данные"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Ищем пользователя в базе
        cursor.execute("""
            SELECT full_name, phone_number 
            FROM users 
            WHERE username = ?
        """, (username,))

        result = cursor.fetchone()

        if result :
            # Пользователь найден, возвращаем его данные
            full_name = result[0]
            phone = result[1] if len(result) > 1 else None

            if full_name and not phone:
                return False, None, None  # Заставляем ввести все заново

            return True, full_name, phone
        else:
            # Пользователь не найден
            return False, None, None


def save_admin_to_db(username, name, phone, chat_id):
    with get_connection() as conn:
        cursor = conn.cursor()

        # Проверяем, есть ли пользователь в базе
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            # Обновляем существующего пользователя
            cursor.execute("""
                UPDATE users 
                SET role = 'head',
                    full_name = ?, 
                    phone_number = ?,
                    created_at = datetime('now')
                WHERE username = ?
            """, (name, phone, username))
            bot.send_message(chat_id,
                             f"✅ {username} назначен администратором\n"
                             f"📛 ФИО: {name}\n"
                             f"📞 Телефон: {phone}")
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (username, full_name, phone_number, role, created_at) 
                VALUES (?, ?, ?, 'head', datetime('now'))
            """, (username, name, phone))
            bot.send_message(chat_id,
                             f"✅ Добавлен администратор:\n"
                             f"👤 Username: {username}\n"
                             f"📛 ФИО: {name}\n"
                             f"📞 Телефон: {phone}\n"
                             f"🎖️ Роль: Администратор (руководитель) студии")
        #Добавляем в таблицу studios студию с данным админом
        user_id = cursor.lastrowid
        cursor.execute("""
                       INSERT INTO studios (name, description, contacts, promo_photo_id, promo_video_id, is_active,
                        head_user_id, invite_code) 
                       VALUES (?, ?, ?, ?, ?,? ,?, ?)
                   """, ("None" , None, None, None , None, 1, user_id , None))

        conn.commit()


