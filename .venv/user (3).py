import telebot
from telebot import types
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging
import re

from users_collector import QuestionnaireBuilder
from вопросы import get_question_text, get_question_obj

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")
DB_PATH = "student_studios_bot (1).db"

def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_active_studios() -> List[Tuple[int, str]]:
    """Загрузка списка активных студий"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT studio_id, name FROM studios WHERE is_active = 1 ORDER BY studio_id")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error loading studios: {e}")
        return []

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Каталог студий')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Мои заявки')
    btn3 = types.KeyboardButton('Подать заявку')
    markup.row(btn2, btn3)

    bot.send_message(
        message.chat.id,
        f'<em>Привет, в этом боте ты можешь узнать про творческие студии'
        f' ГУАП и стать частью активной студенческой жизни!</em>',
        parse_mode='html',
        reply_markup=markup
    )

# ВЕТКА КАТАЛОГ СТУДИЙ

@bot.message_handler(func=lambda message: message.text == 'Каталог студий')
def inline_button_catalog(message):
    studios = load_active_studios()

    if not studios:
        bot.send_message(message.chat.id, 'На данный момент активных студий нет.')
        return

    markup = types.InlineKeyboardMarkup()
    for studio_id, name in studios:
        btn = types.InlineKeyboardButton(name, callback_data=f'info:{studio_id}')
        markup.row(btn)

    bot.send_message(message.chat.id, 'Нажми на студию для просмотра:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('info:'))
def show_studio_info(call):
    """Показывает информацию о студии"""
    studio_id = int(call.data.split(':')[1])

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, description, contacts 
                FROM studios 
                WHERE studio_id = ?
            """, (studio_id,))
            result = cursor.fetchone()

            if result:
                name, description, contacts = result
                text = f"<b>{name}</b>\n\n{description or 'Описание скоро появится.'}\n\n<b>Контакты:</b> {contacts or '—'}"

                # Добавляем кнопку подачи заявки
                markup = types.InlineKeyboardMarkup()
                btn_apply = types.InlineKeyboardButton("📝 Подать заявку", callback_data=f'apply:{studio_id}')
                markup.row(btn_apply)

                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='html',
                    reply_markup=markup
                )
            else:
                bot.answer_callback_query(call.id, "Студия не найдена")
    except Exception as e:
        logger.error(f"Error showing studio info: {e}")
        bot.answer_callback_query(call.id, "Ошибка при загрузке информации")

# Хранение состояний пользователей
user_states = {}

class QuestionnaireHandler:
    """Обработчик анкет с автозаполнением"""

    def __init__(self, db_connection):
        pass

    def start_questionnaire(self, call):
        """Начало анкеты для выбранной студии"""
        studio_id = int(call.data.split(':')[1])
        user_id = call.from_user.id

        # Проверяем, существует ли такая студия в конфигурации
        studio_config = QuestionnaireBuilder.get_questionnaire_for_studio(studio_id)
        if not studio_config:
            bot.answer_callback_query(call.id, f"Анкета для этой студии не настроена")
            return

        # Сохраняем данные в состоянии пользователя
        user_states[user_id] = {
            'state': 'questionnaire',
            'studio_id': studio_id,
            'studio_name': studio_config.get('name', 'Студия'),
            'current_question_index': 0,
            'answers': {},
            'questionnaire': studio_config  # Сохраняем конфигурацию студии
        }

        # Получаем данные пользователя для автозаполнения
        user_data = self.get_user_data(user_id)
        user_states[user_id]['user_data'] = user_data

        # Проверяем возможность автозаполнения
        if QuestionnaireBuilder.can_autofill(studio_id, user_data):
            self.offer_autofill(call, studio_id, user_data)
        else:
            self.start_manual_filling(call, studio_id)

    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получает данные пользователя из БД для автозаполнения"""
        try:
            with get_connection() as conn:  # Открывается соединение
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT full_name, student_group, phone_number, email 
                    FROM users 
                    WHERE telegram_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                return {
                    'full_name': result[0] or '',
                    'student_group': result[1] or '',
                    'phone_number': result[2] or '',
                    'email': result[3] or ''
                } if result else {}
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return {}

    def offer_autofill(self, call, studio_id: int, user_data: Dict[str, Any]):
        """Предлагает автозаполнение"""
        # Получаем поля для автозаполнения
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)
        autofill_info = []

        for field in autofill_fields:
            value = user_data.get(field, '')
            if value:
                field_name = {
                    'full_name': 'ФИО',
                    'student_group': 'Группа',
                    'phone_number': 'Телефон',
                    'email': 'Email'
                }.get(field, field)
                autofill_info.append(f"{field_name}: {value}")

        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        message = f"*Анкета для студии: {studio_name}*\n\n"

        if autofill_info:
            message += "Найдены ваши данные из предыдущих анкет:\n"
            for info in autofill_info:
                message += f"• {info}\n"
            message += "\nХотите использовать их для автозаполнения?"
        else:
            message += "Хотите использовать основную информацию из предыдущих анкет для автозаполнения?"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Использовать мои данные", callback_data='use_autofill'),
            types.InlineKeyboardButton("✏️ Заполнить вручную", callback_data='manual_fill')
        )

        bot.edit_message_text(
            message,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )

    def start_manual_filling(self, call, studio_id: int):
        """Начинает ручное заполнение анкеты"""
        user_id = call.from_user.id
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)

        # Обновляем состояние
        user_states[user_id]['state'] = 'answering'

        bot.edit_message_text(
            f"Начинаем заполнение анкеты для студии *{studio_name}*.\n\n"
            f"Пожалуйста, ответьте на несколько вопросов:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )

        # Даем небольшую задержку перед первым вопросом
        import time
        time.sleep(1)

        # Задаем первый вопрос
        self.ask_next_question(call.message.chat.id, user_id)

    def ask_next_question(self, chat_id: int, user_id: int):
        """Задает следующий вопрос"""
        if user_id not in user_states:
            return

        state = user_states[user_id]
        studio_id = state['studio_id']
        question_ids = QuestionnaireBuilder.get_question_sequence(studio_id)
        current_index = state.get('current_question_index', 0)
        answers = state.get('answers', {})

        # Пропускаем уже заполненные вопросы
        while current_index < len(question_ids):
            qid = question_ids[current_index]
            if qid not in answers:
                break
            current_index += 1

        # Проверяем, не заполнили ли мы все вопросы
        if current_index >= len(question_ids):
            self.show_summary(chat_id, user_id)
            return

        # Сохраняем текущий индекс
        user_states[user_id]['current_question_index'] = current_index
        user_states[user_id]['current_question_id'] = qid

        # Получаем текст вопроса
        question_text = get_question_text(qid)

        # Отправляем вопрос
        bot.send_message(chat_id, question_text)

    def process_answer(self, message):
        """Обработка ответа на вопрос"""
        user_id = message.from_user.id

        if user_id not in user_states:
            return

        state = user_states[user_id]
        if state.get('state') != 'answering':
            return

        current_qid = state.get('current_question_id')
        answer_text = message.text.strip()

        if not current_qid:
            return

        # Получаем объект вопроса для валидации
        q_obj = get_question_obj(current_qid)

        if q_obj:
            is_valid, error_msg = q_obj.validate(answer_text)
            if not is_valid:
                bot.send_message(message.chat.id, f"❌ {error_msg}\n\nПопробуйте еще раз:")
                return

        # Сохраняем ответ
        user_states[user_id]['answers'][current_qid] = answer_text

        # Переходим к следующему вопросу
        user_states[user_id]['current_question_index'] += 1

        # Задаем следующий вопрос
        self.ask_next_question(message.chat.id, user_id)

    def show_summary(self, chat_id: int, user_id: int):
        """Показывает сводку по ответам"""
        if user_id not in user_states:
            return

        state = user_states[user_id]
        studio_id = state['studio_id']
        answers = state.get('answers', {})

        # Валидируем ответы
        is_valid, errors = QuestionnaireBuilder.validate_answers(studio_id, answers)

        if not is_valid:
            error_text = "❌ *Ошибки в заполнении:*\n\n"
            for qid, error in errors.items():
                q_obj = get_question_obj(qid)
                error_text += f"• {q_obj.text if q_obj else qid}: {error}\n"

            error_text += "\nПожалуйста, заполните анкету заново."

            bot.send_message(chat_id, error_text, parse_mode='Markdown')

            # Сбрасываем анкету
            state['current_question_index'] = 0
            state['answers'] = {}

            # Запускаем заново
            self.ask_next_question(chat_id, user_id)
            return

        # Генерируем сводку
        summary = QuestionnaireBuilder.generate_summary(studio_id, answers)

        # Создаем клавиатуру
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Подтвердить и отправить", callback_data='confirm_application'),
            types.InlineKeyboardButton("✏️ Заполнить заново", callback_data='restart_questionnaire')
        )
        markup.row(
            types.InlineKeyboardButton("🚫 Отменить", callback_data='cancel_to_catalog')
        )

        bot.send_message(
            chat_id,
            f"{summary}\n\n*Всё верно? Подтвердите отправку заявки или внесите изменения.*",
            parse_mode='Markdown',
            reply_markup=markup
        )

        # Обновляем состояние
        user_states[user_id]['state'] = 'confirmation'


# Инициализируем обработчик
questionnaire_handler = QuestionnaireHandler(None)

@bot.callback_query_handler(func=lambda call: call.data.startswith('apply:'))
def handle_apply(call):
    """Обработка нажатия кнопки 'Подать заявку'"""
    questionnaire_handler.start_questionnaire(call)

@bot.callback_query_handler(func=lambda call: call.data in ['use_autofill', 'manual_fill'])
def handle_autofill_choice(call):
    """Обработка выбора автозаполнения"""
    user_id = call.from_user.id
    studio_id = user_states[user_id]['studio_id']

    if call.data == 'use_autofill':
        # Автозаполняем данные
        user_data = user_states[user_id]['user_data']
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)

        for field in autofill_fields:
            value = user_data.get(field)
            if value:
                # Находим ID вопроса, соответствующего этому полю
                questions = QuestionnaireBuilder.get_question_objects(studio_id)
                for q in questions:
                    if hasattr(q, 'autofill_field') and q.autofill_field == field:
                        user_states[user_id]['answers'][q.id] = value
                        break

        bot.edit_message_text(
            "✅ Данные автозаполнены.\nПродолжаем с оставшимися вопросами...",
            call.message.chat.id,
            call.message.message_id
        )

    # Начинаем опрос
    user_states[user_id]['state'] = 'answering'
    questionnaire_handler.ask_next_question(call.message.chat.id, user_id)

    def save_application_to_db(telegram_id: int, studio_id: int, answers: dict, user_first_name: str = None,
                               user_last_name: str = None):
        """Сохраняет заявку в БД"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # 1. Получаем или создаем пользователя
                cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
                user_result = cursor.fetchone()

                if user_result:
                    user_id = user_result[0]
                else:
                    # Получаем ФИО из ответов
                    full_name = answers.get('full_name')

                    # Если нет в ответах, используем имя из Telegram
                    if not full_name and user_first_name:
                        full_name = f"{user_first_name or ''} {user_last_name or ''}".strip()
                        if not full_name:
                            full_name = "Не указано"
                    elif not full_name:
                        full_name = "Не указано"

                    # Создаем нового пользователя
                    cursor.execute("""
                        INSERT INTO users (telegram_id, full_name, created_at)
                        VALUES (?, ?, ?)
                    """, (telegram_id, full_name, datetime.now()))
                    user_id = cursor.lastrowid

                # 2. Генерируем сводку
                summary = QuestionnaireBuilder.generate_summary(studio_id, answers)

                # 3. Сохраняем заявку
                cursor.execute("""
                    INSERT INTO applications (user_id, studio_id, summary_text, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, studio_id, summary, 'pending', datetime.now()))

                application_id = cursor.lastrowid

                # 4. Сохраняем ответы на каждый вопрос (опционально)
                for question_id, answer in answers.items():
                    q_obj = get_question_obj(question_id)
                    question_text = q_obj.text if q_obj else question_id

                    cursor.execute("""
                        INSERT INTO application_answers 
                        (application_id, question_id, question_text, answer_text)
                        VALUES (?, ?, ?, ?)
                    """, (application_id, question_id, question_text, answer))

                conn.commit()
                return application_id

        except Exception as e:
            logger.error(f"Error saving application: {e}")
            return None

# ... предыдущий код до функции handle_autofill_choice ...

@bot.callback_query_handler(func=lambda call: call.data in ['use_autofill', 'manual_fill'])
def handle_autofill_choice(call):
    """Обработка выбора автозаполнения"""
    user_id = call.from_user.id
    studio_id = user_states[user_id]['studio_id']

    if call.data == 'use_autofill':
        # Автозаполняем данные
        user_data = user_states[user_id]['user_data']
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)

        for field in autofill_fields:
            value = user_data.get(field)
            if value:
                # Находим ID вопроса, соответствующего этому полю
                questions = QuestionnaireBuilder.get_question_objects(studio_id)
                for q in questions:
                    if hasattr(q, 'autofill_field') and q.autofill_field == field:
                        user_states[user_id]['answers'][q.id] = value
                        break

        bot.edit_message_text(
            "✅ Данные автозаполнены.\nПродолжаем с оставшимися вопросами...",
            call.message.chat.id,
            call.message.message_id
        )

    # Начинаем опрос
    user_states[user_id]['state'] = 'answering'
    questionnaire_handler.ask_next_question(call.message.chat.id, user_id)

# ========== ВЫНЕСИТЕ ЭТИ ФУНКЦИИ НА УРОВЕНЬ ДРУГИХ ФУНКЦИЙ ==========

def save_application_to_db(telegram_id: int, studio_id: int, answers: dict, user_first_name: str = None,
                           user_last_name: str = None):
    """Сохраняет заявку в БД"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Получаем или создаем пользователя
            cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
            user_result = cursor.fetchone()

            if user_result:
                user_id = user_result[0]
            else:
                # Получаем ФИО из ответов
                full_name = answers.get('full_name')

                # Если нет в ответах, используем имя из Telegram
                if not full_name and user_first_name:
                    full_name = f"{user_first_name or ''} {user_last_name or ''}".strip()
                    if not full_name:
                        full_name = "Не указано"
                elif not full_name:
                    full_name = "Не указано"

                # Создаем нового пользователя
                cursor.execute("""
                    INSERT INTO users (telegram_id, full_name, created_at)
                    VALUES (?, ?, ?)
                """, (telegram_id, full_name, datetime.now()))
                user_id = cursor.lastrowid

            # 2. Генерируем сводку
            summary = QuestionnaireBuilder.generate_summary(studio_id, answers)

            # 3. Сохраняем заявку
            cursor.execute("""
                INSERT INTO applications (user_id, studio_id, summary, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, studio_id, summary, 'pending', datetime.now()))

            application_id = cursor.lastrowid

            # 4. Сохраняем ответы на каждый вопрос (опционально)
            for question_id, answer in answers.items():
                q_obj = get_question_obj(question_id)
                question_text = q_obj.text if q_obj else question_id

                cursor.execute("""
                    INSERT INTO application_answers 
                    (application_id, question_id, question_text, answer_text)
                    VALUES (?, ?, ?, ?)
                """, (application_id, question_id, question_text, answer))

            conn.commit()
            return application_id

    except Exception as e:
        logger.error(f"Error saving application: {e}")
        return None

@bot.callback_query_handler(func=lambda call: call.data in [
    'confirm_application', 'restart_questionnaire', 'cancel_to_catalog', 'go_to_main_menu'
])
def handle_confirmation_actions(call):
    """Обработка действий подтверждения"""
    user_id = call.from_user.id

    if user_id not in user_states:
        bot.answer_callback_query(call.id, "Сессия устарела")
        return

    state = user_states[user_id]
    studio_id = state['studio_id']
    answers = state.get('answers', {})

    if call.data == 'confirm_application':
        # СОХРАНЯЕМ В БД с передачей имени пользователя
        application_id = save_application_to_db(
            telegram_id=user_id,
            studio_id=studio_id,
            answers=answers,
            user_first_name=call.from_user.first_name,
            user_last_name=call.from_user.last_name
        )

        if application_id:
            bot.answer_callback_query(call.id, "✅ Заявка отправлена")

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🏠 Главное меню", callback_data='go_to_main_menu'))

            bot.edit_message_text(
                "✅ Ваша заявка отправлена успешно!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка при сохранении")

            bot.edit_message_text(
                "❌ Произошла ошибка при сохранении заявки. Попробуйте позже.",
                call.message.chat.id,
                call.message.message_id
            )

        # Очищаем состояние
        del user_states[user_id]

    elif call.data == 'restart_questionnaire':
        # Начинаем заново
        state['current_question_index'] = 0
        state['answers'] = {}
        state['state'] = 'answering'

        bot.edit_message_text(
            "Начинаем заполнение анкеты заново...",
            call.message.chat.id,
            call.message.message_id
        )

        import time
        time.sleep(1)

        questionnaire_handler.ask_next_question(call.message.chat.id, user_id)

    elif call.data == 'cancel_to_catalog':
        # Отменяем и возвращаем в каталог
        if user_id in user_states:
            del user_states[user_id]

        # Загружаем студии и показываем каталог
        studios = load_active_studios()
        if studios:
            markup = types.InlineKeyboardMarkup()
            for studio_id, name in studios:
                btn = types.InlineKeyboardButton(name, callback_data=f'info:{studio_id}')
                markup.row(btn)

            bot.edit_message_text(
                "Заполнение анкеты отменено.\n\nВыберите студию:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.edit_message_text(
                "Заполнение анкеты отменено.",
                call.message.chat.id,
                call.message.message_id
            )

    elif call.data == 'go_to_main_menu':
        # Возвращаем в главное меню
        if user_id in user_states:
            del user_states[user_id]

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Каталог студий')
        markup.row(btn1)
        btn2 = types.KeyboardButton('Мои заявки')
        btn3 = types.KeyboardButton('Подать заявку')
        markup.row(btn2, btn3)

        bot.edit_message_text(
            "Вы вернулись в главное меню.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )

        bot.send_message(
            call.message.chat.id,
            f'<em>Привет! В этом боте ты можешь узнать про творческие студии'
            f' ГУАП и стать частью активной студенческой жизни!</em>',
            parse_mode='html',
            reply_markup=markup
        )


# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_text_messages(message):
    """Обработка всех текстовых сообщений"""
    user_id = message.from_user.id

    # Проверяем, находится ли пользователь в процессе заполнения анкеты
    if user_id in user_states and user_states[user_id].get('state') == 'answering':
        questionnaire_handler.process_answer(message)
        return

    # Обработка других команд
    if message.text == 'Мои заявки':
        bot.send_message(message.chat.id, "Функция 'Мои заявки' в разработке")
    elif message.text == 'Подать заявку':
        inline_button_catalog(message)
    else:
        bot.send_message(message.chat.id, "Используйте кнопки меню или команду /start")

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)


