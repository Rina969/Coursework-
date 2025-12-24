import telebot
from telebot import types
import logging
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")



def get_connection(db_path: str = "bd2.db") -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные пользователя по Telegram ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT user_id,
                                  username,
                                  full_name,
                                  phone_number,
                                  role,
                                  student_group,
                                  telegram_id,
                                  email
                           FROM users
                           WHERE telegram_id = ?
                           """, (str(telegram_id),))
            result = cursor.fetchone()

            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'full_name': result[2],
                    'phone_number': result[3],
                    'role': result[4],
                    'student_group': result[5],
                    'telegram_id': result[6],
                    'email': result[7]
                }
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя: {e}")
    return None


def get_studio_by_head_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Получает студию по ID руководителя"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT studio_id,
                                  name,
                                  description,
                                  contacts,
                                  promo_photo_id,
                                  promo_video_id,
                                  is_active,
                                  head_user_id,
                                  invite_code
                           FROM studios
                           WHERE head_user_id = ?
                           """, (user_id,))
            result = cursor.fetchone()

            if result:
                return {
                    'studio_id': result[0],
                    'name': result[1],
                    'description': result[2],
                    'contacts': result[3],
                    'promo_photo_id': result[4],
                    'promo_video_id': result[5],
                    'is_active': bool(result[6]),
                    'head_user_id': result[7],
                    'invite_code': result[8]
                }
    except Exception as e:
        logger.error(f"Ошибка получения студии: {e}")
    return None


def get_studio_statistics(studio_id: int) -> Dict[str, int]:
    """Получает статистику по заявкам студии"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT COUNT(*)                                             as total,
                                  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END)  as pending,
                                  SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                                  SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                           FROM applications
                           WHERE studio_id = ?
                           """, (studio_id,))

            stats_row = cursor.fetchone()

            return {
                'total': stats_row[0] if stats_row else 0,
                'pending': stats_row[1] if stats_row else 0,
                'accepted': stats_row[2] if stats_row else 0,
                'rejected': stats_row[3] if stats_row else 0
            }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {'total': 0, 'pending': 0, 'accepted': 0, 'rejected': 0}


def update_studio_info(studio_id: int, description: str = None, contacts: str = None) -> bool:
    """Обновляет информацию о студии"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if description and contacts:
                cursor.execute("""
                               UPDATE studios
                               SET description = ?,
                                   contacts    = ?
                               WHERE studio_id = ?
                               """, (description, contacts, studio_id))
            elif description:
                cursor.execute("""
                               UPDATE studios
                               SET description = ?
                               WHERE studio_id = ?
                               """, (description, studio_id))
            elif contacts:
                cursor.execute("""
                               UPDATE studios
                               SET contacts = ?
                               WHERE studio_id = ?
                               """, (contacts, studio_id))

            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Ошибка обновления информации студии: {e}")
        return False


def get_pending_applications(studio_id: int) -> List[Dict[str, Any]]:
    """Получает ожидающие заявки для студии"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT a.application_id,
                                  a.summary,
                                  a.created_at,
                                  u.user_id,
                                  u.full_name,
                                  u.student_group,
                                  u.username,
                                  u.phone_number,
                                  u.email,
                                  u.telegram_id
                           FROM applications a
                                    JOIN users u ON a.user_id = u.user_id
                           WHERE a.studio_id = ?
                             AND a.status = 'pending'
                           ORDER BY a.created_at ASC
                           """, (studio_id,))

            rows = cursor.fetchall()
            applications = []

            for row in rows:
                applications.append({
                    'application_id': row[0],
                    'summary': row[1],
                    'created_at': row[2],
                    'user_id': row[3],
                    'full_name': row[4],
                    'student_group': row[5],
                    'username': row[6],
                    'phone_number': row[7],
                    'email': row[8],
                    'student_telegram_id': row[9]
                })

            return applications
    except Exception as e:
        logger.error(f"Ошибка получения заявок: {e}")
        return []


def get_application_details(application_id: int) -> Optional[Dict[str, Any]]:
    """Получает детальную информацию о заявке"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT a.application_id,
                                  a.summary,
                                  a.status,
                                  a.created_at,
                                  u.full_name,
                                  u.student_group,
                                  u.username,
                                  u.phone_number,
                                  u.email,
                                  u.telegram_id,
                                  s.name as studio_name,
                                  s.studio_id
                           FROM applications a
                                    JOIN users u ON a.user_id = u.user_id
                                    JOIN studios s ON a.studio_id = s.studio_id
                           WHERE a.application_id = ?
                           """, (application_id,))

            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute("""
                           SELECT question_text, answer_text
                           FROM application_answers
                           WHERE application_id = ?
                           ORDER BY created_at
                           """, (application_id,))

            answers = cursor.fetchall()
            answers_dict = {question: answer for question, answer in answers}

            return {
                'application_id': row[0],
                'summary': row[1],
                'status': row[2],
                'created_at': row[3],
                'full_name': row[4],
                'student_group': row[5],
                'username': row[6],
                'phone_number': row[7],
                'email': row[8],
                'student_telegram_id': row[9],
                'studio_name': row[10],
                'studio_id': row[11],
                'answers': answers_dict
            }
    except Exception as e:
        logger.error(f"Ошибка получения деталей заявки: {e}")
        return None


def update_application_status(application_id: int, status: str) -> bool:
    """Обновляет статус заявки"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE applications
                           SET status     = ?,
                               updated_at = ?
                           WHERE application_id = ?
                           """, (status, datetime.now(), application_id))

            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Ошибка обновления статуса заявки: {e}")
        return False



def create_head_menu() -> types.ReplyKeyboardMarkup:
    """Создает меню для руководителя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_new_applications = types.KeyboardButton('Новые заявки')
    btn_statistics = types.KeyboardButton('Статистика')
    btn_edit_studio = types.KeyboardButton('Изменить информацию о студии')
    btn_refresh = types.KeyboardButton('Обновить')

    markup.row(btn_new_applications, btn_statistics)
    markup.row(btn_edit_studio)
    markup.row(btn_refresh)

    return markup


def create_student_menu() -> types.ReplyKeyboardMarkup:
    """Создает меню для студента"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_catalog = types.KeyboardButton('Каталог студий')
    btn_my_applications = types.KeyboardButton('Мои заявки')
    btn_new_application = types.KeyboardButton('Подать заявку')

    markup.row(btn_catalog)
    markup.row(btn_my_applications, btn_new_application)

    return markup


def create_head_inline_menu() -> types.InlineKeyboardMarkup:
    """Создает inline-меню для руководителя"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_new_applications = types.InlineKeyboardButton('Новые заявки', callback_data='head_new_applications')
    btn_statistics = types.InlineKeyboardButton('Статистика', callback_data='head_statistics')
    btn_edit_studio = types.InlineKeyboardButton('Изменить информацию', callback_data='head_edit_studio')

    markup.add(btn_new_applications, btn_statistics)
    markup.add(btn_edit_studio)

    return markup

review_states = {}
edit_states = {}



def handle_head_start(message: types.Message) -> bool:
    """Обработка входа руководителя"""
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name

    logger.info(f"=== ВХОД РУКОВОДИТЕЛЯ: telegram_id={telegram_id} ({first_name}) ===")

    # Проверяем, является ли руководителем
    studio_data = get_head_studio_data(telegram_id)

    if not studio_data:
        return False

    # Показать приветственное сообщение
    studio_name = studio_data['name']
    stats = get_studio_statistics(studio_data['studio_id'])

    welcome_message = (
        f"<b>Добро пожаловать, {first_name}!</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n\n"
        f"<b>Статистика заявок:</b>\n"
        f"Всего: {stats.get('total', 0)}\n"
        f"Ожидают: {stats.get('pending', 0)}\n"
        f"✅ Принято: {stats.get('accepted', 0)}\n"
        f"❌ Отклонено: {stats.get('rejected', 0)}\n\n"
    )

    markup = create_head_menu()

    bot.send_message(
        message.chat.id,
        welcome_message,
        parse_mode='HTML',
        reply_markup=markup
    )

    logger.info(f"✅ Показано меню руководителя для студии '{studio_name}'")
    return True


def get_head_studio_data(telegram_id: int) -> Optional[dict]:
    """Получает данные студии для руководителя"""
    user_data = get_user_by_telegram_id(telegram_id)

    if not user_data or user_data['role'] != 'head':
        logger.info(f"❌ Пользователь {telegram_id} не является руководителем")
        return None

    studio_data = get_studio_by_head_id(user_data['user_id'])

    if not studio_data:
        logger.warning(f"У руководителя {telegram_id} не назначена студия")
        return None

    return studio_data


def handle_statistics(message: types.Message):
    """Обработка кнопки статистики"""
    telegram_id = message.from_user.id

    logger.info(f"=== СТАТИСТИКА ОТ telegram_id={telegram_id} ===")

    # Проверяем, является ли руководителем
    studio_data = get_head_studio_data(telegram_id)
    if not studio_data:
        send_access_denied(message.chat.id)
        return

    # Получаем статистику
    stats = get_studio_statistics(studio_data['studio_id'])
    studio_name = studio_data['name']

    message_text = (
        f"<b>Статистика по заявкам</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n\n"
        f"<b>Общая статистика:</b>\n"
        f"📋 Всего заявок: {stats.get('total', 0)}\n"
        f"Ожидают рассмотрения: {stats.get('pending', 0)}\n"
        f"✅ Принято: {stats.get('accepted', 0)}\n"
        f"❌ Отклонено: {stats.get('rejected', 0)}\n\n"
    )

    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode='HTML'
    )


def handle_edit_studio_info(message: types.Message):
    """Обработка кнопки изменения информации о студии"""
    telegram_id = message.from_user.id

    logger.info(f"=== ИЗМЕНЕНИЕ ИНФОРМАЦИИ ОТ telegram_id={telegram_id} ===")

    # Проверяем, является ли руководителем
    studio_data = get_head_studio_data(telegram_id)
    if not studio_data:
        send_access_denied(message.chat.id)
        return

    # Сохраняем состояние редактирования
    edit_states[telegram_id] = {
        'action': 'editing_studio',
        'studio_id': studio_data['studio_id'],
        'step': 'description'
    }

    studio_name = studio_data['name']
    current_description = studio_data.get('description', 'Не указано')
    current_contacts = studio_data.get('contacts', 'Не указаны')

    edit_message = (
        f"<b>Изменение информации о студии</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n\n"
        f"<b>Текущее описание:</b>\n{current_description}\n\n"
        f"<b>Текущие контакты:</b>\n{current_contacts}\n\n"
        f"<b>Шаг 1 из 2:</b> Введите новое описание студии (или напишите 'пропустить' чтобы оставить текущее):"
    )

    bot.send_message(
        message.chat.id,
        edit_message,
        parse_mode='HTML'
    )


def handle_edit_description(message: types.Message):
    """Обработка ввода нового описания"""
    telegram_id = message.from_user.id

    if telegram_id not in edit_states or edit_states[telegram_id]['action'] != 'editing_studio':
        return

    studio_id = edit_states[telegram_id]['studio_id']
    new_description = message.text.strip()

    if new_description.lower() == 'пропустить':
        new_description = None
        edit_states[telegram_id]['new_description'] = None
    else:
        edit_states[telegram_id]['new_description'] = new_description

    edit_states[telegram_id]['step'] = 'contacts'

    next_message = (
        f"<b>Шаг 2 из 2:</b> Введите новые контакты студии\n"
        f"(или напишите 'пропустить' чтобы оставить текущие):"
    )

    bot.send_message(
        message.chat.id,
        next_message,
        parse_mode='HTML'
    )


def handle_edit_contacts(message: types.Message):
    """Обработка ввода новых контактов"""
    telegram_id = message.from_user.id

    if telegram_id not in edit_states or edit_states[telegram_id]['action'] != 'editing_studio':
        return

    new_contacts = message.text.strip()
    studio_id = edit_states[telegram_id]['studio_id']

    if new_contacts.lower() == 'пропустить':
        new_contacts = None

    new_description = edit_states[telegram_id].get('new_description')

    # Обновляем информацию в БД
    success = update_studio_info(studio_id, new_description, new_contacts)

    if success:
        result_message = "✅ Информация о студии успешно обновлена!"
        logger.info(f"✅ Обновлена информация о студии {studio_id}")
    else:
        result_message = "❌ Ошибка при обновлении информации"
        logger.error(f"❌ Ошибка обновления информации студии {studio_id}")

    # Очищаем состояние
    if telegram_id in edit_states:
        del edit_states[telegram_id]

    bot.send_message(
        message.chat.id,
        result_message,
        parse_mode='HTML'
    )

    # Возвращаем в главное меню с inline кнопками
    return_to_head_menu_with_inline(message.chat.id)


def send_access_denied(chat_id: int):
    """Отправляет сообщение об отказе в доступе"""
    bot.send_message(
        chat_id,
        "❌ <b>Доступ запрещен</b>\n\n"
        "Эта функция доступна только руководителям студий.",
        parse_mode='HTML'
    )


def return_to_head_menu_with_inline(chat_id: int):
    """Возвращает в главное меню руководителя с inline кнопками"""
    markup = create_head_menu()
    inline_markup = create_head_inline_menu()

    bot.send_message(
        chat_id,
        "<b>Вы вернулись в главное меню руководителя</b>\n\n",
        parse_mode='HTML',
        reply_markup=markup
    )

    bot.send_message(
        chat_id,
        "<b>Быстрые действия:</b>",
        parse_mode='HTML',
        reply_markup=inline_markup
    )


def format_application_message(app_data: Dict[str, Any], current_num: int, total: int) -> str:
    """Форматирует сообщение с информацией о заявке"""
    message = f"<b>Заявка #{app_data['application_id']}</b>\n\n"
    message += f"<b>Студент:</b> {app_data['full_name']}\n"

    if app_data.get('student_group'):
        message += f"<b>Группа:</b> {app_data['student_group']}\n"

    if app_data.get('username'):
        message += f"<b>Telegram:</b> @{app_data['username']}\n"

    if app_data.get('phone_number'):
        message += f"<b>Телефон:</b> {app_data['phone_number']}\n"

    if app_data.get('email'):
        message += f"<b>Email:</b> {app_data['email']}\n"

    message += f"\n<b>Сводка:</b>\n{app_data.get('summary', 'Нет сводки')}\n"

    message += f"\n<i>Прогресс: {current_num} из {total}</i>"

    return message


def start_reviewing_applications(telegram_id: int, studio_id: int, chat_id: int) -> bool:
    """Начинает просмотр заявок руководителем"""
    try:
        applications = get_pending_applications(studio_id)

        if not applications:
            logger.info(f"ℹНет новых заявок для студии {studio_id}")
            return False

        review_states[telegram_id] = {
            'studio_id': studio_id,
            'applications': applications,
            'current_index': 0,
            'chat_id': chat_id,
            'status': 'reviewing'
        }

        # Убираем навигационное сообщение, сразу показываем первую заявку
        show_next_application(chat_id, telegram_id)
        return True

    except Exception as e:
        logger.error(f"Ошибка начала просмотра для руководителя {telegram_id}: {e}")
        return False


def show_next_application(chat_id: int, telegram_id: int):
    """Показывает следующую заявку в очереди"""
    if telegram_id not in review_states:
        return

    state = review_states[telegram_id]
    applications = state['applications']
    current_index = state['current_index']

    if current_index >= len(applications):
        bot.send_message(
            chat_id,
            "🎉 <b>Все заявки рассмотрены!</b>\n\n"
            "Новых заявок в очереди нет.",
            parse_mode='HTML'
        )

        del review_states[telegram_id]
        return_to_head_menu_with_inline(chat_id)
        return

    app_data = applications[current_index]
    app_id = app_data['application_id']

    details = get_application_details(app_id)

    if not details:
        bot.send_message(
            chat_id,
            f"Ошибка загрузки заявки #{app_id}. Пропускаем...",
            parse_mode='HTML'
        )
        state['current_index'] += 1
        show_next_application(chat_id, telegram_id)
        return

    state['current_application_id'] = app_id

    message_text = format_application_message(details, current_index + 1, len(applications))

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept:{app_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{app_id}")
    )

    # Изменено с "Связаться" на "Пропустить"
    markup.add(
        types.InlineKeyboardButton("Пропустить", callback_data=f"skip:{app_id}"),
        types.InlineKeyboardButton("Прекратить", callback_data="stop_review")
    )

    bot.send_message(
        chat_id,
        message_text,
        parse_mode='HTML',
        reply_markup=markup
    )


def send_notification_to_student(student_telegram_id: str, student_name: str, studio_name: str, action: str):
    """Отправляет уведомление студенту"""
    try:
        if not student_telegram_id:
            return

        if action == 'accepted':
            message = (
                f"🎉 <b>Поздравляем, {student_name}!</b>\n\n"
                f"Ваша заявка в студию <b>'{studio_name}'</b> одобрена!\n\n"
                f"Руководитель свяжется с вами для дальнейших инструкций."
            )
        elif action == 'rejected':
            message = (
                f"<b>Уважаемый(ая) {student_name}!</b>\n\n"
                f"К сожалению, ваша заявка в студию <b>'{studio_name}'</b> отклонена.\n\n"
                f"Не расстраивайтесь! Вы можете подать заявку в другие студии."
            )
        else:
            return

        bot.send_message(
            student_telegram_id,
            message,
            parse_mode='HTML'
        )

        logger.info(f"✅ Уведомление отправлено студенту {student_telegram_id}")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления студенту: {e}")


def remove_processed_application(telegram_id: int, application_id: int):
    """Удаляет обработанную заявку из состояния пользователя"""
    if telegram_id not in review_states:
        return

    state = review_states[telegram_id]
    applications = state['applications']

    new_applications = [
        app for app in applications
        if app['application_id'] != application_id
    ]

    state['applications'] = new_applications

    if state['current_index'] >= len(new_applications):
        state['current_index'] = 0


def move_application_to_end(telegram_id: int, application_id: int):
    """Перемещает заявку в конец очереди"""
    if telegram_id not in review_states:
        return

    state = review_states[telegram_id]
    applications = state['applications']

    target_app = None
    other_apps = []

    for app in applications:
        if app['application_id'] == application_id:
            target_app = app
        else:
            other_apps.append(app)

    if target_app:
        state['applications'] = other_apps + [target_app]
        state['current_index'] = 0


def handle_application_action(call):
    """Обрабатывает действия руководителя с заявками"""
    telegram_id = call.from_user.id

    if telegram_id not in review_states:
        bot.answer_callback_query(call.id, "Сессия устарела. Начните просмотр заново.")
        return

    action_data = call.data
    state = review_states[telegram_id]

    if action_data == "stop_review":
        bot.answer_callback_query(call.id, "Просмотр прекращен")

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        del review_states[telegram_id]
        return_to_head_menu_with_inline(call.message.chat.id)
        return

    parts = action_data.split(":")
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "Ошибка обработки")
        return

    action, app_id_str = parts
    app_id = int(app_id_str)

    if state.get('current_application_id') != app_id:
        bot.answer_callback_query(call.id, "Заявка уже обработана")
        return

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if action == "accept":
        accept_application(call, app_id, telegram_id)
    elif action == "reject":
        reject_application(call, app_id, telegram_id)
    elif action == "skip":  # Изменено с "contact" на "skip"
        skip_application(call, app_id, telegram_id)


def accept_application(call, application_id: int, telegram_id: int):
    """Принять заявку"""
    try:
        app_data = get_application_details(application_id)
        if not app_data:
            bot.answer_callback_query(call.id, "❌ Ошибка при принятии")
            return

        success = update_application_status(application_id, 'accepted')

        if success:
            send_notification_to_student(
                app_data['student_telegram_id'],
                app_data['full_name'],
                app_data['studio_name'],
                'accepted'
            )

            bot.answer_callback_query(call.id, "✅ Заявка принята")

            remove_processed_application(telegram_id, application_id)
            state = review_states[telegram_id]
            show_next_application(state['chat_id'], telegram_id)
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка при принятии")

    except Exception as e:
        logger.error(f"Ошибка принятия заявки {application_id}: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при принятии")


def reject_application(call, application_id: int, telegram_id: int):
    """Отклонить заявку"""
    try:
        app_data = get_application_details(application_id)
        if not app_data:
            bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")
            return

        success = update_application_status(application_id, 'rejected')

        if success:
            send_notification_to_student(
                app_data['student_telegram_id'],
                app_data['full_name'],
                app_data['studio_name'],
                'rejected'
            )

            bot.answer_callback_query(call.id, "❌ Заявка отклонена")

            remove_processed_application(telegram_id, application_id)
            state = review_states[telegram_id]
            show_next_application(state['chat_id'], telegram_id)
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")

    except Exception as e:
        logger.error(f"Ошибка отклонения заявки {application_id}: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")


def skip_application(call, application_id: int, telegram_id: int):
    """Пропустить заявку (переместить в конец)"""
    try:
        bot.answer_callback_query(call.id, "Заявка пропущена")

        move_application_to_end(telegram_id, application_id)
        state = review_states[telegram_id]
        show_next_application(state['chat_id'], telegram_id)

    except Exception as e:
        logger.error(f"Ошибка пропуска заявки {application_id}: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка")


# ==================== ОБРАБОТЧИКИ INLINE КНОПОК ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith('head_'))
def handle_head_inline_callbacks(call):
    """Обработка inline кнопок руководителя"""
    action = call.data

    if action == 'head_new_applications':
        handle_new_applications_inline(call)
    elif action == 'head_statistics':
        handle_statistics_inline(call)
    elif action == 'head_edit_studio':
        handle_edit_studio_inline(call)


def handle_new_applications_inline(call):
    """Обработка inline кнопки 'Новые заявки'"""
    telegram_id = call.from_user.id

    user_data = get_user_by_telegram_id(telegram_id)
    if not user_data or user_data['role'] != 'head':
        bot.answer_callback_query(call.id, "❌ Доступ запрещен")
        return

    studio_data = get_studio_by_head_id(user_data['user_id'])
    if not studio_data:
        bot.answer_callback_query(call.id, "❌ У вас не назначена студия")
        return

    if telegram_id in review_states:
        bot.answer_callback_query(call.id, "Просмотр уже начат")
        return

    success = start_reviewing_applications(
        telegram_id,
        studio_data['studio_id'],
        call.message.chat.id
    )

    if not success:
        bot.answer_callback_query(call.id, "✅ Нет новых заявок")
        bot.send_message(
            call.message.chat.id,
            "✅ <b>Нет новых заявок</b>\n\n"
            "Все заявки уже рассмотрены или новых пока нет.",
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "Начинаем просмотр заявок")


def handle_statistics_inline(call):
    """Обработка inline кнопки 'Статистика'"""
    telegram_id = call.from_user.id

    studio_data = get_head_studio_data(telegram_id)
    if not studio_data:
        bot.answer_callback_query(call.id, "❌ Доступ запрещен")
        return

    stats = get_studio_statistics(studio_data['studio_id'])
    studio_name = studio_data['name']

    message_text = (
        f"<b>Статистика по заявкам</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n\n"
        f"<b>Общая статистика:</b>\n"
        f"Всего заявок: {stats.get('total', 0)}\n"
        f"Ожидают рассмотрения: {stats.get('pending', 0)}\n"
        f"✅ Принято: {stats.get('accepted', 0)}\n"
        f"❌ Отклонено: {stats.get('rejected', 0)}"
    )

    bot.answer_callback_query(call.id, "Статистика загружена")
    bot.send_message(
        call.message.chat.id,
        message_text,
        parse_mode='HTML'
    )


def handle_edit_studio_inline(call):
    """Обработка inline кнопки 'Изменить информацию'"""
    telegram_id = call.from_user.id

    studio_data = get_head_studio_data(telegram_id)
    if not studio_data:
        bot.answer_callback_query(call.id, "❌ Доступ запрещен")
        return

    edit_states[telegram_id] = {
        'action': 'editing_studio',
        'studio_id': studio_data['studio_id'],
        'step': 'description'
    }

    studio_name = studio_data['name']
    current_description = studio_data.get('description', 'Не указано')
    current_contacts = studio_data.get('contacts', 'Не указаны')

    edit_message = (
        f"<b>Изменение информации о студии</b>\n\n"
        f"<b>Студия:</b> {studio_name}\n\n"
        f"<b>Текущее описание:</b>\n{current_description}\n\n"
        f"<b>Текущие контакты:</b>\n{current_contacts}\n\n"
        f"<b>Шаг 1 из 2:</b> Введите новое описание студии (или напишите 'пропустить' чтобы оставить текущее):"
    )

    bot.answer_callback_query(call.id, "Режим редактирования")
    bot.send_message(
        call.message.chat.id,
        edit_message,
        parse_mode='HTML'
    )


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Главная команда запуска бота"""
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name

    logger.info(f"=== КОМАНДА /start ОТ telegram_id={telegram_id} ({first_name}) ===")

    is_head = handle_head_start(message)

    if not is_head:
        markup = create_student_menu()

        bot.send_message(
            message.chat.id,
            f"👨‍🎓 <b>Добро пожаловать, {first_name}!</b>\n\n"
            f"<b>Роль:</b> Студент\n\n"
            f"Выберите действие в меню ниже:",
            parse_mode='HTML',
            reply_markup=markup
        )
        logger.info(f"✅ Показано меню студента для {telegram_id}")


@bot.message_handler(func=lambda message: message.text == 'Новые заявки')
def handle_new_applications(message):
    """Начало просмотра заявок руководителем"""
    telegram_id = message.from_user.id

    logger.info(f"=== КНОПКА 'НОВЫЕ ЗАЯВКИ' ОТ telegram_id={telegram_id} ===")

    user_data = get_user_by_telegram_id(telegram_id)
    if not user_data or user_data['role'] != 'head':
        bot.send_message(
            message.chat.id,
            "❌ <b>Доступ запрещен</b>\n\n"
            "Эта функция доступна только руководителям студий.",
            parse_mode='HTML'
        )
        return

    studio_data = get_studio_by_head_id(user_data['user_id'])
    if not studio_data:
        bot.send_message(
            message.chat.id,
            "❌ <b>Ошибка</b>\n\n"
            "У вас не назначена студия.",
            parse_mode='HTML'
        )
        return

    if telegram_id in review_states:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Просмотр уже начат</b>\n\n"
            "Завершите текущий просмотр перед началом нового.",
            parse_mode='HTML'
        )
        return

    logger.info(f"✅ Запуск просмотра заявок для студии {studio_data['studio_id']}")

    success = start_reviewing_applications(
        telegram_id,
        studio_data['studio_id'],
        message.chat.id
    )

    if not success:
        bot.send_message(
            message.chat.id,
            "✅ <b>Нет новых заявок</b>\n\n"
            "Все заявки уже рассмотрены или новых пока нет.",
            parse_mode='HTML'
        )


@bot.message_handler(func=lambda message: message.text == 'Статистика')
def handle_statistics_button(message):
    """Обработка кнопки статистики"""
    handle_statistics(message)


@bot.message_handler(func=lambda message: message.text == 'Изменить информацию о студии')
def handle_edit_studio_button(message):
    """Обработка кнопки изменения информации о студии"""
    handle_edit_studio_info(message)


@bot.message_handler(func=lambda message: message.text == 'Обновить')
def handle_refresh(message):
    """Обновление информации"""
    telegram_id = message.from_user.id

    logger.info(f"=== КНОПКА 'ОБНОВИТЬ' ОТ telegram_id={telegram_id} ===")

    user_data = get_user_by_telegram_id(telegram_id)

    if user_data and user_data['role'] == 'head':
        studio_data = get_studio_by_head_id(user_data['user_id'])

        if studio_data:
            stats = get_studio_statistics(studio_data['studio_id'])
            studio_name = studio_data['name']

            markup = create_head_menu()
            inline_markup = create_head_inline_menu()

            response = (
                f"✅ <b>Информация обновлена</b>\n\n"
                f"<b>Студия:</b> {studio_name}\n"
                f"<b>Новых заявок:</b> {stats.get('pending', 0)}\n"
                f"<b>Всего заявок:</b> {stats.get('total', 0)}\n\n"
            )

            bot.send_message(
                message.chat.id,
                response,
                parse_mode='HTML',
                reply_markup=markup
            )

            bot.send_message(
                message.chat.id,
                "Выберите действие:",
                parse_mode='HTML',
                reply_markup=inline_markup
            )

            logger.info(f"✅ Обновлено меню руководителя")
        else:
            markup = create_head_menu()
            response = "❌ <b>У вас не назначена студия</b>"

            bot.send_message(
                message.chat.id,
                response,
                parse_mode='HTML',
                reply_markup=markup
            )
    else:
        markup = create_student_menu()
        response = "✅ <b>Информация обновлена</b>"

        bot.send_message(
            message.chat.id,
            response,
            parse_mode='HTML',
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith(('accept:', 'reject:', 'skip:')) or
                                              call.data == 'stop_review')
def handle_review_callbacks(call):
    """Обработка callback-ов от просмотра заявок"""
    logger.info(f"=== CALLBACK: {call.data} от telegram_id={call.from_user.id} ===")
    handle_application_action(call)


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех остальных сообщений"""
    telegram_id = message.from_user.id

    if telegram_id in review_states:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Вы в режиме просмотра заявок</b>\n\n"
            "Используйте кнопки под заявкой для действий.",
            parse_mode='HTML'
        )
        return

    if telegram_id in edit_states:
        state = edit_states[telegram_id]

        if state['action'] == 'editing_studio':
            if state['step'] == 'description':
                handle_edit_description(message)
            elif state['step'] == 'contacts':
                handle_edit_contacts(message)
            return

    user_data = get_user_by_telegram_id(telegram_id)

    if user_data and user_data['role'] == 'head':
        markup = create_head_menu()
        response = "<b>Главное меню руководителя</b>"
    else:
        markup = create_student_menu()
        response = "<b>Главное меню студента</b>"

    bot.send_message(
        message.chat.id,
        response,
        parse_mode='HTML',
        reply_markup=markup
    )


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("БОТ ЗАПУЩЕН")
    logger.info("=" * 50)

    bot.polling(none_stop=True)








#
# from gettext import textdomain
#
# import telebot
# from telebot import types
# import sqlite3
# from typing import Optional, List, Tuple
# from datetime import datetime
# import logging
#
# from studio_manager import StudioManager
#
# #В коде логгер нигде не используется???
# logging.basicConfig(
#     # %(asctime)s — время события
#     # %(name)s — имя логгера (модуля)
#     # %(levelname)s — уровень важности (INFO, ERROR, WARNING)
#     # %(message)s — текст сообщения
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# # на уровне INFO: запуск/остановка процессов, критические действия пользователей, ошибки доступа,но не обычные действия пользователей
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)
#
# bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")
#
# # Инициализируем менеджер студии
# studio_manager = StudioManager(bot)
# user_sessions = {} # Хранит активные сессии руководителей
#
# studio_manager.user_states = {}  # Хранит состояние просмотра заявок
#
# #======================
# #====HEAD OF STUDIO====
# #======================
# def cleanup_stale_sessions():
#     #Очистка зависших сессий более чем на час - пока не решила куда вставить
#     current_time = datetime.now()
#     stale_users = []
#
#     for user_id, session in user_sessions.items():
#         if (current_time - session['start_time']).seconds > 3600:  # 1 час
#             stale_users.append(user_id)
#
#     for user_id in stale_users:
#         del user_sessions[user_id]
#         if user_id in studio_manager.user_states:
#             del studio_manager.user_states[user_id]
#         logger.warning(f"Очищена зависшая сессия пользователя {user_id}")
#
# def show_main_menu(markup):
#     btn1 = types.KeyboardButton('')
#     btn2=types.KeyboardButton('Новые заявки')
#     markup.row(btn1, btn2)
#     btn3 = types.KeyboardButton('Изменить информацию о студии')
#
#
# def get_connection() -> sqlite3.Connection:
#     """Возвращает соединение с БД"""
#     return sqlite3.connect("student_studios_bot.db", check_same_thread=False)
#
# def create_main_menu_markup(user_id: int = None) -> types.ReplyKeyboardMarkup:
#     """Создает главное меню руководителя"""
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
#
#
#     btn_statistics = types.KeyboardButton('Отчет по заявкам')
#     btn_applications = types.KeyboardButton("Новые заявки")
#     markup.row(btn_statistics, btn_applications)
#
#     btn_refresh = types.KeyboardButton('Обновить')
#     markup.row(btn_refresh)
#
#     return markup
#
# @bot.message_handler(commands=['head'])
# def handle_head_start(message):
#     """Обработчик команды для входа руководителя"""
#     user_id = message.from_user.id
#     first_name = message.from_user.first_name
#
#     studio_id = studio_manager.get_studio_id_for_head(user_id)
#
#     if not studio_id:
#         bot.send_message(
#             message.chat.id,
#             "❌ <b>Доступ запрещен</b>\n\n"
#             "Вы не зарегистрированы как руководитель студии.",
#             parse_mode='HTML'
#         )
#         return
#
#     # Получаем название студии
#     studio_name = studio_manager.get_studio_name(studio_id)
#
#     # Получаем количество ожидающих заявок
#     applications = studio_manager.get_new_applications(studio_id)
#     pending_count = len(applications)
#
#     welcome_message = (
#         f"👋 <b>Добро пожаловать, {first_name}!</b>\n\n"
#     )
#
#     # Отправляем главное меню
#     markup = create_main_menu_markup(user_id)
#     bot.send_message(
#         message.chat.id,
#         welcome_message,
#         parse_mode='HTML',
#         reply_markup=markup
#     )
#
# @bot.message_handler(func=lambda message: message.text.startswith('📋 Новые заявки'))
# def handle_applications_start(message):
#     """Начало просмотра заявок"""
#     user_id = message.from_user.id
#
#     # Проверяем, не идет ли уже просмотр
#     if user_id in studio_manager.user_states:
#         bot.send_message(
#             message.chat.id,
#             "⚠️ <b>Просмотр уже начат</b>\n\n"
#             "Завершите текущий просмотр или нажмите 'Прекратить просмотр'.",
#             parse_mode='HTML'
#         )
#         return
#
#     studio_id = studio_manager.get_studio_id_for_head(user_id)
#     if not studio_id:
#         bot.send_message(
#             message.chat.id,
#             "❌ 1Ошибка доступа",
#             parse_mode='HTML'
#         )
#         return
#
#     # Получаем название студии
#     studio_name = studio_manager.get_studio_name(studio_id)
#     success = studio_manager.start_reviewing_applications_with_id(user_id, studio_id)
#
#     if not success:
#         return
#
#     # Запускаем сессию
#     user_sessions[user_id] = {
#         'start_time': datetime.now(),
#         'studio_name': studio_name,
#         'total_applications': len(studio_manager.user_states[user_id]['applications']),
#         'processed': 0,
#         'accepted': 0,
#         'rejected': 0
#     }
#
#     # Информационное сообщение
#     state = studio_manager.user_states[user_id]
#     total_apps = len(state['applications'])
#
#     bot.send_message(
#         message.chat.id,
#         f"<b>Начинаем просмотр заявок</b>\n\n"
#         f"<b>Студия:</b> {studio_name}\n"
#         f"<b>Всего заявок:</b> {total_apps}\n",
#         parse_mode='HTML'
#     )
#
#     # Показываем первую заявку
#     studio_manager.show_next_application(message.chat.id, user_id)
#
# @bot.message_handler(func=lambda message: message.text == 'отчет по заявкам')
# def handle_statistics(message):
#     user_id = message.from_user.id
#
#     studio_id = studio_manager.get_studio_id_for_head(user_id)
#     if not studio_id:
#         bot.send_message(
#             message.chat.id,
#             "❌ 2Ошибка доступа",
#             parse_mode='HTML'
#         )
#         return
#
#     stats = studio_manager.get_statistics(studio_id)
#     studio_name = studio_manager.get_studio_name(studio_id)
#
#     # Форматируем сообщение
#     message_text = studio_manager.format_statistics_message(stats, studio_name)
#
#
#
# @bot.message_handler(func=lambda message: message.text == 'Обновить')
# def handle_refresh(message):
#     """Обновление списка заявок"""
#     user_id = message.from_user.id
#     print(user_id)
#
#     studio_id = studio_manager.get_studio_id_for_head(user_id)
#     if not studio_id:
#         bot.send_message(
#             message.chat.id,
#             "❌ 3Ошибка доступа",
#             parse_mode='HTML'
#         )
#         return
#
#     # Получаем актуальный список заявок
#     applications = studio_manager.get_new_applications(studio_id)
#     studio_name = studio_manager.get_studio_name(studio_id)
#
#     # Обновляем меню
#     markup = create_main_menu_markup(user_id)
#
#     if applications:
#         message_text = (
#             f"<b>Список заявок обновлен</b>\n\n"
#             f"<b>Заявок в очереди:</b> {len(applications)}\n\n"
#             f"<i>Нажмите 'Новые заявки' для начала просмотра</i>"
#         )
#     else:
#         message_text = (
#             f"<b>Список заявок обновлен</b>\n\n"
#             f"<b>Заявок в очереди:</b> 0\n\n"
#             f"<i>Новых заявок пока нет</i>"
#         )
#
#     bot.send_message(
#         message.chat.id,
#         message_text,
#         parse_mode='HTML',
#         reply_markup=markup
#     )
#
# @bot.message_handler(func=lambda message: message.text == 'Главное меню')
# def handle_main_menu(message):
#     """Возврат в главное меню"""
#     user_id = message.from_user.id
#
#     # Очищаем состояние просмотра
#     if user_id in studio_manager.user_states:
#         del studio_manager.user_states[user_id]
#
#
#         del user_sessions[user_id]
#
#     # Возвращаем главное меню
#     markup = create_main_menu_markup(user_id)
#     bot.send_message(
#         message.chat.id,
#         "🏠 <b>Главное меню руководителя</b>",
#         parse_mode='HTML',
#         reply_markup=markup
#     )
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith(('accept:', 'reject:', 'skip:')) or
#                            call.data == 'stop_review')
# def handle_review_callbacks(call):
#     """Обработка callback-ов от просмотра заявок"""
#     user_id = call.from_user.id
#
#     # Обновляем статистику сессии
#     if user_id in user_sessions:
#         session = user_sessions[user_id]
#
#         if call.data.startswith('accept:'):
#             session['accepted'] += 1
#             session['processed'] += 1
#         elif call.data.startswith('reject:'):
#             session['rejected'] += 1
#             session['processed'] += 1
#         elif call.data.startswith('skip:'):
#             session['processed'] += 1
#
#     # Передаем обработку в менеджер студии
#     studio_manager.handle_application_action(call)
#
# @bot.message_handler(func=lambda message: True)
# def handle_other_messages(message):
#     """Обработчик всех других сообщений"""
#     user_id = message.from_user.id
#
#     # Если пользователь в режиме просмотра
#     if user_id in studio_manager.user_states:
#         bot.send_message(
#             message.chat.id,
#             "⚠️ <b>Вы в режиме просмотра заявок</b>\n\n"
#             "Используйте кнопки под заявкой для действий.",
#             parse_mode='HTML'
#         )
#     else:
#         # Проверяем, является ли руководителем
#        # studio_id = studio_manager.get_studio_id_for_head(user_id)
#         studio_id = True
#
#         if studio_id:
#             # Показываем меню руководителя
#             markup = create_main_menu_markup(user_id)
#             bot.send_message(
#                 message.chat.id,
#                 "<b>Главное меню руководителя</b>",
#                 parse_mode='HTML',
#                 reply_markup=markup
#             )
#         else:
#             # Показываем обычное меню
#             markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#             btn1 = types.KeyboardButton('Каталог студий')
#             markup.row(btn1)
#             btn2 = types.KeyboardButton('Мои заявки')
#             btn3 = types.KeyboardButton('Подать заявку')
#             markup.row(btn2, btn3)
#
#             bot.send_message(
#                 message.chat.id,
#                 "👋 <b>Добро пожаловать в бот студенческих студий!</b>",
#                 parse_mode='HTML',
#                 reply_markup=markup
#             )



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


