from gettext import textdomain

from typing import Optional
import telebot
from telebot import types
import uuid             # Для генерации уникальных имен файлов
from datetime import datetime  # Для работы с датами и временем
import sqlite3 as sq
import os

# Импортируем bot из основного файла (будет установлен в initialize)
bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

def get_connection():
    # Путь к вашей базе данных
    db_path = os.path.join(os.path.dirname(__file__), 'student_studios_bot (1).db')
    conn = sq.connect(db_path)
    return conn
#======================
#========ADMIN=========
#======================
# Функция инициализации модуля
def initialize(bot_instance):
    global bot
    bot = bot_instance
    print("Admin module initialized")
    return bot

def admin_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Статистика')
    btn2 = types.KeyboardButton('Рассылка')
    btn3 = types.KeyboardButton('Назначить администратора')
    markup.row(btn1, btn2, btn3)
    btn4 = types.KeyboardButton('Изменить информацию о студиях')
    markup.row(btn4)

    bot.send_message(message.chat.id,
                     f'<em> Добро пожаловать, {message.from_user.first_name}.</em>',
                     parse_mode='html',
                     reply_markup=markup)

# Регистрация всех хендлеров администратора

# Функции-обработчики (без декораторов!)
def handle_statistics(message):
    """Обработчик кнопки 'Статистика'"""
    bot.send_message(message.chat.id, f'<em>Статистика активности:</em>', parse_mode='html')

def handle_broadcast(message):
    """Обработчик кнопки 'Рассылка'"""
    bot.send_message(message.chat.id, f'<em>Введите сообщение:</em>', parse_mode='html')

def handle_give_role(message):
    """Обработчик кнопки 'Назначить администратора'"""
    bot.send_message(message.chat.id, "Перешлите сообщение пользователя или введите @username")
    bot.register_next_step_handler(message, get_admin_username)


# Главный обработчик для админа
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_admin_message(message):
    """Обрабатывает сообщения для админа"""
    if not message.text:
        return False

    text=message.text
    print(text)
    # Обработка кнопок из admin_start
    if text == 'Статистика':
        handle_statistics(message)
        return True

    elif text == 'Рассылка':
        handle_broadcast(message)
        # Для рассылки нужно обработать следующий шаг
        # Это можно сделать через bot.register_next_step_handler
        bot.register_next_step_handler(message, process_broadcast)
        return True

    elif text == 'Назначить администратора':
        handle_give_role(message)
        # Следующий шаг - получение username
        bot.register_next_step_handler(message, get_admin_username)
        return True

    elif text == 'Изменить информацию о студиях':
        handle_studio_info(message)
        return True

    else:
        # Если сообщение не обработано
        return False

#Надо забирать еще айдишник в тг
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

        # Получаем или создаем telegram_id для пользователя
        # В пересланных сообщениях используем forward_from.id, в текстовом вводе - нужно получить ID пользователя
        # chat_id - это ID чата отправителя (обычно совпадает с user_id для личных чатов)

        telegram_id = None

        # Проверяем, есть ли пользователь в базе
        if '@' in username:
            # Если username начинается с @
            clean_username = username.replace('@', '')
            cursor.execute("SELECT telegram_id FROM users WHERE username LIKE ?", (f'%{clean_username}%',))
            result = cursor.fetchone()

            if result:
                telegram_id = result[0]
            else:
                # Для новых пользователей используем chat_id как telegram_id
                telegram_id = chat_id
        else:
            # Если username - это число (ID)
            try:
                telegram_id = int(username)
            except ValueError:
                telegram_id = chat_id

        # Проверяем, существует ли пользователь с таким telegram_id
        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = ?", (telegram_id,))
        user_exists = cursor.fetchone()[0] > 0

        if user_exists:
            # Обновляем существующего пользователя
            cursor.execute("""
                UPDATE users 
                SET username = ?,
                    role = 'head',
                    full_name = ?, 
                    phone_number = ?,
                    created_at = datetime('now')
                WHERE telegram_id = ?
            """, (username, name, phone, telegram_id))
            bot.send_message(chat_id,
                             f"✅ Пользователь обновлен как администратор\n"
                             f"🆔 Telegram ID: {telegram_id}\n"
                             f"👤 Username: {username}\n"
                             f"📛 ФИО: {name}\n"
                             f"📞 Телефон: {phone}")
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (telegram_id, username, full_name, phone_number, role, created_at) 
                VALUES (?, ?, ?, ?, 'head', datetime('now'))
            """, (telegram_id, username, name, phone))
            bot.send_message(chat_id,
                             f"✅ Добавлен администратор:\n"
                             f"🆔 Telegram ID: {telegram_id}\n"
                             f"👤 Username: {username}\n"
                             f"📛 ФИО: {name}\n"
                             f"📞 Телефон: {phone}\n"
                             f"🎖️ Роль: Администратор (руководитель) студии")

        # Теперь добавляем в таблицу studios, используя telegram_id как head_user_id
        cursor.execute("""
            INSERT INTO studios (name, description, contacts, promo_photo_id, 
                                promo_video_id, is_active, head_user_id, invite_code) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"Студия {name}", f"Студия под руководством {name}",
              phone, None, None, 1, telegram_id, None))

        conn.commit()


# def save_admin_to_db(username, name, phone, chat_id):
#     with get_connection() as conn:
#         cursor = conn.cursor()
#
#         # Проверяем, есть ли пользователь в базе
#         cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
#         user = cursor.fetchone()
#
#         if user:
#             # Обновляем существующего пользователя
#             cursor.execute("""
#                 UPDATE users
#                 SET role = 'head',
#                     full_name = ?,
#                     phone_number = ?,
#                     created_at = datetime('now')
#                 WHERE username = ?
#             """, (name, phone, username))
#             bot.send_message(chat_id,
#                              f"✅ {username} назначен администратором\n"
#                              f"📛 ФИО: {name}\n"
#                              f"📞 Телефон: {phone}")
#         else:
#             # Добавляем нового пользователя
#             cursor.execute("""
#                 INSERT INTO users (username, full_name, phone_number, role, created_at)
#                 VALUES (?, ?, ?, 'head', datetime('now'))
#             """, (username, name, phone))
#             bot.send_message(chat_id,
#                              f"✅ Добавлен администратор:\n"
#                              f"👤 Username: {username}\n"
#                              f"📛 ФИО: {name}\n"
#                              f"📞 Телефон: {phone}\n"
#                              f"🎖️ Роль: Администратор (руководитель) студии")
#         #Добавляем в таблицу studios студию с данным админом
#         user_id = cursor.lastrowid
#         cursor.execute("""
#                        INSERT INTO studios (name, description, contacts, promo_photo_id, promo_video_id, is_active,
#                         head_user_id, invite_code)
#                        VALUES (?, ?, ?, ?, ?,? ,?, ?)
#                    """, ("None" , None, None, None , None, 0, user_id , None))
#
#         conn.commit()


