from gettext import textdomain

import telebot
from telebot import types
import sqlite3
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from studio_manager import StudioManager

#В коде логгер нигде не используется???
logging.basicConfig(
    # %(asctime)s — время события
    # %(name)s — имя логгера (модуля)
    # %(levelname)s — уровень важности (INFO, ERROR, WARNING)
    # %(message)s — текст сообщения
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# на уровне INFO: запуск/остановка процессов, критические действия пользователей, ошибки доступа,но не обычные действия пользователей
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

# Инициализируем менеджер студии
studio_manager = StudioManager(bot)
user_sessions = {} # Хранит активные сессии руководителей

studio_manager.user_states = {}  # Хранит состояние просмотра заявок

#======================
#====HEAD OF STUDIO====
#======================
def cleanup_stale_sessions():
    #Очистка зависших сессий более чем на час - пока не решила куда вставить
    current_time = datetime.now()
    stale_users = []

    for user_id, session in user_sessions.items():
        if (current_time - session['start_time']).seconds > 3600:  # 1 час
            stale_users.append(user_id)

    for user_id in stale_users:
        del user_sessions[user_id]
        if user_id in studio_manager.user_states:
            del studio_manager.user_states[user_id]
        logger.warning(f"Очищена зависшая сессия пользователя {user_id}")

def show_main_menu(markup):
    btn1 = types.KeyboardButton('')
    btn2=types.KeyboardButton('Новые заявки')
    markup.row(btn1, btn2)
    btn3 = types.KeyboardButton('Изменить информацию о студии')


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect("student_studios_bot (1).db", check_same_thread=False)

def create_main_menu_markup(user_id: int = None) -> types.ReplyKeyboardMarkup:
    """Создает главное меню руководителя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    
    btn_statistics = types.KeyboardButton('Отчет по заявкам')
    btn_applications = types.KeyboardButton("Новые заявки")
    markup.row(btn_statistics, btn_applications)
    
    btn_refresh = types.KeyboardButton('Обновить')
    markup.row(btn_refresh)
    
    return markup

@bot.message_handler(commands=['head'])
def handle_head_start(message):
    """Обработчик команды для входа руководителя"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    studio_id = studio_manager.get_studio_id_for_head(user_id)
    
    if not studio_id:
        bot.send_message(
            message.chat.id,
            "❌ <b>Доступ запрещен</b>\n\n"
            "Вы не зарегистрированы как руководитель студии.",
            parse_mode='HTML'
        )
        return
    
    # Получаем название студии
    studio_name = studio_manager.get_studio_name(studio_id)
    
    # Получаем количество ожидающих заявок
    applications = studio_manager.get_new_applications(studio_id)
    pending_count = len(applications)
    
    welcome_message = (
        f"👋 <b>Добро пожаловать, {first_name}!</b>\n\n"
    )
    
    # Отправляем главное меню
    markup = create_main_menu_markup(user_id)
    bot.send_message(
        message.chat.id,
        welcome_message,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text.startswith('📋 Новые заявки'))
def handle_applications_start(message):
    """Начало просмотра заявок"""
    user_id = message.from_user.id
    
    # Проверяем, не идет ли уже просмотр
    if user_id in studio_manager.user_states:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Просмотр уже начат</b>\n\n"
            "Завершите текущий просмотр или нажмите 'Прекратить просмотр'.",
            parse_mode='HTML'
        )
        return
    
    studio_id = studio_manager.get_studio_id_for_head(user_id)
    if not studio_id:
        bot.send_message(
            message.chat.id,
            "❌ 1Ошибка доступа",
            parse_mode='HTML'
        )
        return
    
    # Получаем название студии
    studio_name = studio_manager.get_studio_name(studio_id)
    success = studio_manager.start_reviewing_applications_with_id(user_id, studio_id)
    
    if not success:
        return
    
    # Запускаем сессию
    user_sessions[user_id] = {
        'start_time': datetime.now(),
        'studio_name': studio_name,
        'total_applications': len(studio_manager.user_states[user_id]['applications']),
        'processed': 0,
        'accepted': 0,
        'rejected': 0
    }
    
    # Информационное сообщение
    state = studio_manager.user_states[user_id]
    total_apps = len(state['applications'])
    
    bot.send_message(
        message.chat.id,
        f"<b>Начинаем просмотр заявок</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n"
        f"<b>Всего заявок:</b> {total_apps}\n",
        parse_mode='HTML'
    )
    
    # Показываем первую заявку
    studio_manager.show_next_application(message.chat.id, user_id)

@bot.message_handler(func=lambda message: message.text == 'отчет по заявкам')
def handle_statistics(message):
    user_id = message.from_user.id
    
    studio_id = studio_manager.get_studio_id_for_head(user_id)
    if not studio_id:
        bot.send_message(
            message.chat.id,
            "❌ 2Ошибка доступа",
            parse_mode='HTML'
        )
        return
    
    stats = studio_manager.get_statistics(studio_id)
    studio_name = studio_manager.get_studio_name(studio_id)
    
    # Форматируем сообщение
    message_text = studio_manager.format_statistics_message(stats, studio_name)
    


@bot.message_handler(func=lambda message: message.text == 'Обновить')
def handle_refresh(message):
    """Обновление списка заявок"""
    user_id = message.from_user.id
    print(user_id)
    
    studio_id = studio_manager.get_studio_id_for_head(user_id)
    if not studio_id:
        bot.send_message(
            message.chat.id,
            "❌ 3Ошибка доступа",
            parse_mode='HTML'
        )
        return
    
    # Получаем актуальный список заявок
    applications = studio_manager.get_new_applications(studio_id)
    studio_name = studio_manager.get_studio_name(studio_id)
    
    # Обновляем меню
    markup = create_main_menu_markup(user_id)
    
    if applications:
        message_text = (
            f"<b>Список заявок обновлен</b>\n\n"
            f"<b>Заявок в очереди:</b> {len(applications)}\n\n"
            f"<i>Нажмите 'Новые заявки' для начала просмотра</i>"
        )
    else:
        message_text = (
            f"<b>Список заявок обновлен</b>\n\n"
            f"<b>Заявок в очереди:</b> 0\n\n"
            f"<i>Новых заявок пока нет</i>"
        )
    
    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == 'Главное меню')
def handle_main_menu(message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    
    # Очищаем состояние просмотра
    if user_id in studio_manager.user_states:
        del studio_manager.user_states[user_id]
    
        
        del user_sessions[user_id]
    
    # Возвращаем главное меню
    markup = create_main_menu_markup(user_id)
    bot.send_message(
        message.chat.id,
        "🏠 <b>Главное меню руководителя</b>",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith(('accept:', 'reject:', 'skip:')) or 
                           call.data == 'stop_review')
def handle_review_callbacks(call):
    """Обработка callback-ов от просмотра заявок"""
    user_id = call.from_user.id
    
    # Обновляем статистику сессии
    if user_id in user_sessions:
        session = user_sessions[user_id]
        
        if call.data.startswith('accept:'):
            session['accepted'] += 1
            session['processed'] += 1
        elif call.data.startswith('reject:'):
            session['rejected'] += 1
            session['processed'] += 1
        elif call.data.startswith('skip:'):
            session['processed'] += 1
    
    # Передаем обработку в менеджер студии
    studio_manager.handle_application_action(call)

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработчик всех других сообщений"""
    user_id = message.from_user.id
    
    # Если пользователь в режиме просмотра
    if user_id in studio_manager.user_states:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Вы в режиме просмотра заявок</b>\n\n"
            "Используйте кнопки под заявкой для действий.",
            parse_mode='HTML'
        )
    else:
        # Проверяем, является ли руководителем
       # studio_id = studio_manager.get_studio_id_for_head(user_id)
        studio_id = True
        
        if studio_id:
            # Показываем меню руководителя
            markup = create_main_menu_markup(user_id)
            bot.send_message(
                message.chat.id,
                "<b>Главное меню руководителя</b>",
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            # Показываем обычное меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Каталог студий')
            markup.row(btn1)
            btn2 = types.KeyboardButton('Мои заявки')
            btn3 = types.KeyboardButton('Подать заявку')
            markup.row(btn2, btn3)
            
            bot.send_message(
                message.chat.id,
                "👋 <b>Добро пожаловать в бот студенческих студий!</b>",
                parse_mode='HTML',
                reply_markup=markup
            )



# # ---------------------------ИЗМЕНЕНИЕ ИНФОРМАЦИИ О СТУДИИ---------------------------
#
# @bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
# # ====================
# # РЕДАКТИРОВАНИЕ СТУДИИ
# # ====================
#
# @bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
# def edit_info(message):
#     """
#     Обработчик кнопки 'Изменить информацию о студии'.
#     Начинает процесс пошагового редактирования студии.
#     """
#     user_id = message.from_user.id
#
#     # Начинаем процесс редактирования через наш класс StudioEditor
#     response = studio_editor.start_editing(user_id)
#
#     # Отправляем первое сообщение с инструкцией
#     bot.send_message(
#         message.chat.id,
#         response,
#         parse_mode='html'
#     )
#
#
# @bot.message_handler(func=lambda message: studio_editor.get_user_step(message.from_user.id) in
#                                           ['waiting_for_name', 'waiting_for_description'])
# def handle_text_for_editing(message):
#     """
#     Обработчик текстовых сообщений во время редактирования студии.
#
#     Этот обработчик срабатывает ТОЛЬКО когда пользователь находится
#     на этапе 'waiting_for_name' или 'waiting_for_description'.
#     """
#     user_id = message.from_user.id
#
#     # Передаем текст сообщения в редактор студии
#     response, is_completed = studio_editor.handle_message(user_id, message.text)
#
#     # Отправляем ответ пользователю
#     bot.send_message(
#         message.chat.id,
#         response,
#         parse_mode='html'
#     )
#
#     # Если процесс редактирования завершен, показываем главное меню
#     if is_completed:
#         # Показываем кнопки для дальнейших действий
#         markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#         show_main_menu(markup)
#
#         bot.send_message(
#             message.chat.id,
#             "Что дальше?",
#             reply_markup=markup
#         )
#
#
# @bot.message_handler(content_types=['photo'])
# def handle_photo_for_editing(message):
#     """
#     Обработчик фото во время редактирования студии.
#
#     Этот обработчик срабатывает, когда пользователь отправляет фото.
#     Проверяем, находится ли пользователь на этапе ожидания изображения.
#     """
#     user_id = message.from_user.id
#
#     # Проверяем, находится ли пользователь на этапе ожидания изображения
#     if studio_editor.get_user_step(user_id) != 'waiting_for_image':
#         # Если нет - игнорируем фото или сообщаем об ошибке
#         return
#
#     # Получаем информацию о самом большом фото (Telegram отправляет несколько размеров)
#     file_id = message.photo[-1].file_id
#
#     # Скачиваем фото с серверов Telegram
#     file_info = bot.get_file(file_id)
#     image_bytes = bot.download_file(file_info.file_path)
#
#     # Передаем изображение в редактор студии
#     response, is_completed = studio_editor.handle_image(user_id, image_bytes)
#
#     # Отправляем ответ пользователю
#     bot.send_message(
#         message.chat.id,
#         response,
#         parse_mode='html'
#     )
#
#
# @bot.message_handler(commands=['cancel'])
# def cancel_editing(message):
#     """
#     Обработчик команды /cancel для отмены редактирования.
#     """
#     user_id = message.from_user.id
#     response = studio_editor.cancel_editing(user_id)
#
#     # Возвращаем в главное меню
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     show_main_menu(markup)
#
#     bot.send_message(
#         message.chat.id,
#         response,
#         parse_mode='html',
#         reply_markup=markup
#     )

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
