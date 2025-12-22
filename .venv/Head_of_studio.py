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
user_edit_states = {}  # Добавляем словарь для состояний редактирования
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


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect("student_studios_bot (1).db", check_same_thread=False)

def create_main_menu_markup(user_id: int = None) -> types.ReplyKeyboardMarkup:
    """Создает главное меню руководителя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_statistics = types.KeyboardButton('Отчет по заявкам')
    btn_applications = types.KeyboardButton("Новые заявки")
    markup.row(btn_statistics, btn_applications)

    btn_edit = types.KeyboardButton('Изменить информацию о студии')
    btn_refresh = types.KeyboardButton('Обновить')
    markup.row(btn_refresh)
    markup.row(btn_edit)
    return markup


@bot.message_handler(commands=['head'])
def handle_head_start(message):
    """Обработчик команды для входа руководителя"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    print(f"\n=== DEBUG /head команда ===")
    print(f"Пользователь: {user_id} ({first_name})")

    studio_id = studio_manager.get_studio_id_for_head(user_id)
    print(f"studio_id из базы: {studio_id}")

    if not studio_id:
        print("Пользователь не найден как руководитель в базе данных")
        bot.send_message(
            message.chat.id,
            "❌ <b>Доступ запрещен</b>\n\n"
            "Вы не зарегистрированы как руководитель студии.\n\n"
            f"Ваш ID: {user_id}",
            parse_mode='HTML'
        )
        return

    # Получаем название студии
    studio_name = studio_manager.get_studio_name(studio_id)
    print(f"Название студии: {studio_name}")

    # Получаем количество ожидающих заявок
    applications = studio_manager.get_new_applications(studio_id)
    pending_count = len(applications)

    welcome_message = (
        f"👋 <b>Добро пожаловать, {first_name}!</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n"
        f"<b>Ожидающих заявок:</b> {pending_count}"
    )

    # Отправляем главное меню
    markup = create_main_menu_markup(user_id)
    bot.send_message(
        message.chat.id,
        welcome_message,
        parse_mode='HTML',
        reply_markup=markup
    )
    print("=== Конец /head команды ===\n")

@bot.message_handler(func=lambda message: message.text == "Новые заявки")
def handle_applications_start(message):
    """Начало просмотра заявок"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    print(f"\n=== DEBUG: Начало просмотра заявок ===")
    print(f"Время: {datetime.now()}")
    print(f"Пользователь ID: {user_id}")
    print(f"Chat ID: {chat_id}")

    # Проверяем, не идет ли уже просмотр
    if user_id in studio_manager.user_states:
        print(f"Ошибка: у пользователя {user_id} уже есть активный просмотр")
        bot.send_message(
            chat_id,
            "⚠️ <b>Просмотр заявок уже начат</b>\n\n"
            "Завершите текущий просмотр или нажмите 'Прекратить просмотр'.",
            parse_mode='HTML'
        )
        return

    # Получаем studio_id с детальной отладкой
    print(f"Вызов studio_manager.get_studio_id_for_head({user_id})...")
    studio_id = studio_manager.get_studio_id_for_head(user_id)
    print(f"Полученный studio_id: {studio_id}")

    if not studio_id:
        print(f"ОШИБКА: studio_id не найден для пользователя {user_id}")

        # Детальная диагностика проблемы
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # 1. Проверяем таблицу studios
            cursor.execute("""
                SELECT studio_id, name, head_user_id 
                FROM studios 
                WHERE head_user_id = ?
            """, (user_id,))
            studio_result = cursor.fetchone()
            print(f"Результат прямого SQL запроса в studios: {studio_result}")

            if studio_result:
                print(f"Найдена студия: ID={studio_result[0]}, Название={studio_result[1]}, Head={studio_result[2]}")
            else:
                print(f"Запись в studios с head_user_id={user_id} НЕ НАЙДЕНА")

                # Показываем все студии для отладки
                cursor.execute("SELECT studio_id, name, head_user_id FROM studios ORDER BY studio_id")
                all_studios = cursor.fetchall()
                print(f"Все студии в базе ({len(all_studios)} шт.):")
                for studio in all_studios:
                    print(f"  ID: {studio[0]}, Название: '{studio[1]}', Руководитель: {studio[2]}")

            # 2. Проверяем таблицу users
            cursor.execute("SELECT user_id, full_name, role FROM users WHERE user_id = ?", (user_id,))
            user_result = cursor.fetchone()
            print(f"Запись в users: {user_result}")

            if user_result:
                print(f"Пользователь найден: {user_result[1]}, роль: {user_result[2]}")
            else:
                print(f"ВНИМАНИЕ: Пользователь с ID={user_id} не найден в таблице users")

        except Exception as e:
            print(f"Ошибка при диагностике: {e}")
        finally:
            conn.close()

        # Отправляем информативное сообщение об ошибке
        error_message = (
            f"❌ <b>Ошибка доступа</b>\n\n"
            f"<b>Ваш Telegram ID:</b> {user_id}\n"
            f"<b>ID студии:</b> {studio_id or 'Не найден'}\n\n"
            f"<i>Возможные причины:</i>\n"
            f"1. Вы не привязаны к студии как руководитель\n"
            f"2. Ваш ID ({user_id}) не указан в поле head_user_id\n"
            f"3. Студия не активирована (is_active = 0)\n\n"
            f"<b>Решение:</b>\n"
            f"• Обратитесь к администратору\n"
            f"• Используйте команду /check_access для диагностики"
        )

        bot.send_message(
            chat_id,
            error_message,
            parse_mode='HTML'
        )
        return

    # Успешно получили studio_id - продолжаем
    print(f"УСПЕХ: Найдена студия ID={studio_id}")

    # Получаем название студии
    studio_name = studio_manager.get_studio_name(studio_id)
    print(f"Название студии: '{studio_name}'")

    # Запускаем просмотр заявок
    print(f"Вызов studio_manager.start_reviewing_applications_with_id({user_id}, {studio_id})...")
    success = studio_manager.start_reviewing_applications_with_id(user_id, studio_id)

    if not success:
        print(f"Ошибка: start_reviewing_applications_with_id вернула False")
        bot.send_message(
            chat_id,
            "❌ <b>Не удалось начать просмотр</b>\n\n"
            "Возможно, возникла ошибка при загрузке заявок.",
            parse_mode='HTML'
        )
        return

    print(f"Просмотр успешно запущен. Состояние пользователя создано.")

    # Проверяем, создано ли состояние
    if user_id not in studio_manager.user_states:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: состояние пользователя не создано")
        bot.send_message(
            chat_id,
            "❌ <b>Внутренняя ошибка</b>\n\n"
            "Не удалось инициализировать сессию просмотра.",
            parse_mode='HTML'
        )
        return

    # Получаем информацию о заявках
    state = studio_manager.user_states[user_id]
    applications = state.get('applications', [])
    total_apps = len(applications)

    print(f"Загружено заявок: {total_apps}")

    # Создаем сессию для статистики
    user_sessions[user_id] = {
        'start_time': datetime.now(),
        'studio_name': studio_name,
        'studio_id': studio_id,
        'total_applications': total_apps,
        'processed': 0,
        'accepted': 0,
        'rejected': 0,
        'skipped': 0
    }

    print(f"Сессия создана: {user_sessions[user_id]}")

    # Отправляем информационное сообщение
    if total_apps > 0:
        welcome_message = (
            f"<b>Начинаем просмотр заявок</b>\n\n"
            f"<b>Студия:</b> {studio_name}\n"
            f"<b>Всего заявок:</b> {total_apps}\n\n"
            f"<i>Используйте кнопки для принятия решений:</i>\n"
            f"✅ Принять — одобрить заявку\n"
            f"❌ Отклонить — отказать кандидату\n"
            f"⏭ Пропустить — оставить на потом\n"
            f"Прекратить — завершить просмотр\n\n"
            f"Прогресс отображается внизу каждой заявки."
        )
    else:
        welcome_message = (
            f"<b>Нет новых заявок</b>\n\n"
            f"<b>Студия:</b> {studio_name}\n"
            f"<b>Ожидающих заявок:</b> 0\n\n"
            f"<i>Новых заявок для рассмотрения нет.</i>\n"
            f"Вы можете проверить позже или нажать 'Обновить'."
        )

    bot.send_message(
        chat_id,
        welcome_message,
        parse_mode='HTML'
    )

    # Если есть заявки, показываем первую
    if total_apps > 0:
        print(f"Показываем первую заявку из {total_apps}...")
        studio_manager.show_next_application(chat_id, user_id)
    else:
        # Если заявок нет, очищаем состояние
        print(f"Заявок нет, очищаем состояние...")
        if user_id in studio_manager.user_states:
            del studio_manager.user_states[user_id]
        if user_id in user_sessions:
            del user_sessions[user_id]

        # Возвращаем главное меню
        markup = create_main_menu_markup(user_id)
        bot.send_message(
            chat_id,
            "<b>Возврат в главное меню</b>",
            parse_mode='HTML',
            reply_markup=markup
        )

    print(f"=== DEBUG: Конец обработки ===\n")

@bot.message_handler(func=lambda message: message.text.lower() == 'отчет по заявкам')
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
    bot.send_message(message.chat.id, message_text, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == 'Обновить')
def handle_refresh(message):
    user_id = message.from_user.id
    print(f"\n=== DEBUG Обновление ===")
    print(f"Пользователь: {user_id}")

    studio_id = studio_manager.get_studio_id_for_head(user_id)
    print(f"studio_id: {studio_id}")

    if not studio_id:
        print("Ошибка: studio_id не найден")
        bot.send_message(
            message.chat.id,
            "❌ 3Ошибка доступа\n\n"
            f"User ID: {user_id}\n"
            f"Studio ID: {studio_id}",
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



# # ---------------------------ИЗМЕНЕНИЕ ИНФОРМАЦИИ О СТУДИИ---------------------------

def show_current_studio_info(chat_id: int, studio_id: int):
    """Показывает текущую информацию о студии"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description, contacts FROM studios WHERE id = ?
    """, (studio_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        name, description, contacts = result

        # Форматируем сообщение
        name_display = name if name else '❌ Не указано'
        description_display = description if description else '❌ Не указано'
        contacts_display = contacts if contacts else '❌ Не указаны'

        message = (
            "Текущая информация о студии:\n\n"
            f"Название:\n{name_display}\n\n"
            f"Описание:\n{description_display}\n\n"
            f"Контакты:\n{contacts_display}\n\n"
            "Выберите, что хотите изменить:"
        )
    else:
        message = "Информация о студии не найдена в базе данных"

    bot.send_message(chat_id, message)


def create_edit_menu_markup() -> types.ReplyKeyboardMarkup:
    """Создает меню для редактирования информации о студии"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_name = types.KeyboardButton('Изменить название')
    btn_description = types.KeyboardButton('Изменить описание')
    btn_contacts = types.KeyboardButton('Изменить контакты')
    markup.row(btn_name, btn_description)
    markup.row(btn_contacts)

    btn_save_all = types.KeyboardButton('Сохранить все изменения')
    btn_cancel = types.KeyboardButton('Отмена')
    markup.row(btn_save_all, btn_cancel)

    return markup


def create_main_menu_markup(user_id: int = None) -> types.ReplyKeyboardMarkup:
    """Создает главное меню руководителя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_statistics = types.KeyboardButton('Отчет по заявкам')
    btn_applications = types.KeyboardButton("Новые заявки")
    markup.row(btn_statistics, btn_applications)

    btn_edit = types.KeyboardButton('Изменить информацию о студии')
    btn_refresh = types.KeyboardButton('Обновить')
    markup.row(btn_refresh)
    markup.row(btn_edit)
    return markup


@bot.message_handler(func=lambda message: message.text.lower() == 'изменить информацию о студии')
def handle_edit_studio_start(message):
    """Начало редактирования информации о студии"""
    print(f"КНОПКА НАЖАТА: {message.text}")
    user_id = message.from_user.id
    print(f"Пользователь: {user_id}")

    # Проверяем, не идет ли уже просмотр заявок
    if user_id in studio_manager.user_states:
        print("Пользователь в режиме просмотра")
        bot.send_message(
            message.chat.id,
            "Сначала завершите просмотр заявок"
        )
        return

    studio_id = studio_manager.get_studio_id_for_head(user_id)
    print(f"ID студии: {studio_id}")

    if not studio_id:
        print("Ошибка: studio_id не найден")
        bot.send_message(
            message.chat.id,
            "Ошибка доступа"
        )
        return

    # Инициализируем состояние редактирования
    user_edit_states[user_id] = {
        'studio_id': studio_id,
        'changes': {},
        'awaiting_input': None
    }
    print(f"Создано состояние: {user_edit_states[user_id]}")

    # Показываем текущую информацию
    print("Показываем информацию о студии...")
    show_current_studio_info(message.chat.id, studio_id)

    # Показываем меню редактирования
    print("Показываем меню редактирования...")
    markup = create_edit_menu_markup()
    bot.send_message(
        message.chat.id,
        "Редактирование информации о студии\n\n"
        "Выберите параметр для изменения или 'Сохранить все изменения' для сохранения.",
        reply_markup=markup
    )
    print("Функция завершена")


from Studio_editing import (
    handle_edit_field_selection,
    handle_field_input,
    handle_save_all_changes,
    handle_edit_cancel,
    show_preview
)


@bot.message_handler(func=lambda message: message.text in ['Изменить название', 'Изменить описание', 'Изменить контакты'])
def handle_edit_field(message):
    """Обработка выбора поля для редактирования"""
    handle_edit_field_selection(message, bot, user_edit_states, create_edit_menu_markup)


@bot.message_handler(func=lambda message: user_edit_states.get(message.from_user.id, {}).get('awaiting_input'))
def handle_edit_input(message):
    """Обработка ввода нового значения для поля"""
    handle_field_input(message, bot, user_edit_states, create_edit_menu_markup)

    # Показываем предпросмотр после ввода
    user_id = message.from_user.id
    if user_id in user_edit_states and not user_edit_states[user_id].get('awaiting_input'):
        show_preview(message.chat.id, user_id, bot, user_edit_states)


@bot.message_handler(func=lambda message: message.text == 'Сохранить все изменения')
def handle_save_changes(message):
    """Сохранение всех изменений в БД"""
    handle_save_all_changes(message, bot, user_edit_states, create_main_menu_markup)


@bot.message_handler(func=lambda message: message.text == 'Отмена')
def handle_cancel_edit(message):
    """Отмена редактирования"""
    handle_edit_cancel(message, bot, user_edit_states, create_main_menu_markup)


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

# if __name__ == '__main__':
#     print("Бот запущен...")
#     bot.polling(none_stop=True)
